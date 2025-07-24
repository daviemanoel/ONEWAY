from django.core.management.base import BaseCommand
from django.db import transaction
from pedidos.models import Pedido, ItemPedido, Produto, ProdutoTamanho
import json
import os
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Sincroniza estoque com pedidos aprovados e gera products.json atualizado'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a sincronização sem salvar no banco',
        )
        parser.add_argument(
            '--dias',
            type=int,
            default=7,
            help='Processar pedidos dos últimos N dias (padrão: 7)',
        )
        parser.add_argument(
            '--gerar-json',
            action='store_true',
            help='Gerar products.json após sincronização',
        )
    
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        dias = options.get('dias', 7)
        gerar_json = options.get('gerar_json', False)
        
        # Data limite para processar pedidos
        data_limite = datetime.now() - timedelta(days=dias)
        
        self.stdout.write(self.style.SUCCESS(f'\n{"="*50}'))
        self.stdout.write(self.style.SUCCESS('SINCRONIZAÇÃO DE ESTOQUE'))
        self.stdout.write(self.style.SUCCESS(f'{"="*50}\n'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODO DRY RUN - Nenhuma alteração será salva\n'))
        
        # Estatísticas
        processados = 0
        erros = 0
        sem_estoque = 0
        
        try:
            with transaction.atomic():
                # 1. Processar pedidos NOVOS (com produto_tamanho)
                self.stdout.write(self.style.NOTICE('📦 Processando pedidos do novo sistema...'))
                
                pedidos_novos = Pedido.objects.filter(
                    status_pagamento='approved',
                    estoque_decrementado=False,
                    produto_tamanho__isnull=False,
                    data_pedido__gte=data_limite
                ).select_related('produto_tamanho', 'comprador')
                
                for pedido in pedidos_novos:
                    try:
                        if pedido.produto_tamanho.estoque > 0:
                            if not dry_run:
                                pedido.produto_tamanho.decrementar_estoque(
                                    quantidade=1,
                                    pedido=pedido,
                                    usuario='sistema',
                                    observacao=f'Sincronização automática - Pedido #{pedido.id}',
                                    origem='sincronizar_estoque_comando'
                                )
                                pedido.estoque_decrementado = True
                                pedido.save()
                            
                            self.stdout.write(
                                f"  ✅ Pedido #{pedido.id}: {pedido.produto_tamanho} "
                                f"(estoque: {pedido.produto_tamanho.estoque - 1})"
                            )
                            processados += 1
                        else:
                            self.stdout.write(
                                self.style.ERROR(
                                    f"  ❌ Pedido #{pedido.id}: Sem estoque para {pedido.produto_tamanho}"
                                )
                            )
                            sem_estoque += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"  ❌ Erro no pedido #{pedido.id}: {str(e)}")
                        )
                        erros += 1
                
                # 2. Processar pedidos com MÚLTIPLOS ITENS
                self.stdout.write(self.style.NOTICE('\n🛒 Processando pedidos com múltiplos itens...'))
                
                pedidos_multiplos = Pedido.objects.filter(
                    status_pagamento='approved',
                    estoque_decrementado=False,
                    produto_tamanho__isnull=True,
                    data_pedido__gte=data_limite
                ).prefetch_related('itens__produto_tamanho').select_related('comprador')
                
                for pedido in pedidos_multiplos:
                    if not pedido.itens.exists():
                        continue
                    
                    try:
                        # Verificar se há estoque para todos os itens
                        pode_processar = True
                        itens_sem_estoque = []
                        
                        for item in pedido.itens.all():
                            if item.produto_tamanho:
                                if item.produto_tamanho.estoque < item.quantidade:
                                    pode_processar = False
                                    itens_sem_estoque.append(
                                        f"{item.produto_tamanho} (precisa: {item.quantidade}, tem: {item.produto_tamanho.estoque})"
                                    )
                        
                        if pode_processar:
                            # Decrementar estoque de todos os itens
                            if not dry_run:
                                for item in pedido.itens.all():
                                    if item.produto_tamanho:
                                        item.produto_tamanho.decrementar_estoque(
                                            quantidade=item.quantidade,
                                            pedido=pedido,
                                            usuario='sistema',
                                            observacao=f'Sincronização automática - Pedido #{pedido.id} - Item: {item.get_produto_display()} ({item.tamanho})',
                                            origem='sincronizar_estoque_comando'
                                        )
                                
                                pedido.estoque_decrementado = True
                                pedido.save()
                            
                            self.stdout.write(
                                f"  ✅ Pedido #{pedido.id}: {pedido.itens.count()} itens processados"
                            )
                            processados += 1
                        else:
                            self.stdout.write(
                                self.style.ERROR(
                                    f"  ❌ Pedido #{pedido.id}: Sem estoque para: {', '.join(itens_sem_estoque)}"
                                )
                            )
                            sem_estoque += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"  ❌ Erro no pedido #{pedido.id}: {str(e)}")
                        )
                        erros += 1
                
                # 3. Processar pedidos LEGACY (sem novo sistema)
                self.stdout.write(self.style.NOTICE('\n📊 Processando pedidos legacy...'))
                
                pedidos_legacy = Pedido.objects.filter(
                    status_pagamento='approved',
                    estoque_decrementado=False,
                    produto_tamanho__isnull=True,
                    data_pedido__gte=data_limite
                ).exclude(id__in=pedidos_multiplos).select_related('comprador')
                
                if pedidos_legacy.exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠️  {pedidos_legacy.count()} pedidos legacy encontrados. "
                            "Execute 'python manage.py associar_pedidos_legacy' primeiro."
                        )
                    )
                
                if dry_run:
                    raise Exception('Dry run - rollback')
                
        except Exception as e:
            if dry_run and str(e) == 'Dry run - rollback':
                pass
            else:
                self.stdout.write(self.style.ERROR(f'\n❌ Erro durante sincronização: {str(e)}'))
                raise
        
        # 4. Gerar products.json se solicitado
        if gerar_json and not dry_run:
            self.stdout.write(self.style.NOTICE('\n📄 Gerando products.json...'))
            try:
                self.gerar_products_json()
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erro ao gerar products.json: {str(e)}')
                )
                self.stdout.write(
                    self.style.WARNING('⚠️  Sincronização concluída, mas JSON não foi gerado')
                )
        
        # 5. Resumo final
        self.stdout.write(self.style.SUCCESS(f'\n{"="*50}'))
        self.stdout.write(self.style.SUCCESS('RESUMO DA SINCRONIZAÇÃO:'))
        self.stdout.write(self.style.SUCCESS(f'  ✅ Pedidos processados: {processados}'))
        self.stdout.write(self.style.WARNING(f'  ⚠️  Pedidos sem estoque: {sem_estoque}'))
        self.stdout.write(self.style.ERROR(f'  ❌ Pedidos com erro: {erros}'))
        
        # Estatísticas de estoque
        self.stdout.write(self.style.SUCCESS('\nESTATÍSTICAS DE ESTOQUE:'))
        
        produtos_sem_estoque = ProdutoTamanho.objects.filter(estoque=0)
        produtos_baixo_estoque = ProdutoTamanho.objects.filter(estoque__gt=0, estoque__lte=2)
        
        if produtos_sem_estoque.exists():
            self.stdout.write(self.style.ERROR('\n❌ Produtos ESGOTADOS:'))
            for pt in produtos_sem_estoque.select_related('produto'):
                self.stdout.write(f"   - {pt}")
        
        if produtos_baixo_estoque.exists():
            self.stdout.write(self.style.WARNING('\n⚠️  Produtos com ESTOQUE BAIXO:'))
            for pt in produtos_baixo_estoque.select_related('produto'):
                self.stdout.write(f"   - {pt} (estoque: {pt.estoque})")
        
        self.stdout.write(self.style.SUCCESS(f'{"="*50}\n'))
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS('✅ Sincronização concluída com sucesso!'))
    
    def gerar_products_json(self):
        """Gera o arquivo products.json atualizado"""
        products_data = {"products": {}}
        
        for produto in Produto.objects.filter(ativo=True).order_by('ordem'):
            sizes = {}
            for tamanho in produto.tamanhos.all().order_by('tamanho'):
                sizes[tamanho.tamanho] = {
                    "product_size_id": tamanho.id,
                    "available": tamanho.disponivel and tamanho.estoque > 0,
                    "qtda_estoque": tamanho.estoque,
                    # Campos legacy - buscar do JSON original se existir
                    "stripe_link": None,
                    "id_stripe": f"prod_{produto.json_key}_{tamanho.tamanho.lower()}"
                }
            
            # Determinar imagem correta
            image_map = {
                'camiseta-marrom': './img/camisetas/camiseta_marrom.jpeg',
                'camiseta-jesus': './img/camisetas/Camiseta_jesus.jpeg',
                'camiseta-oneway-branca': './img/camisetas/Camiseta_onewayBranca.jpeg',
                'camiseta-the-way': './img/camisetas/Camiseta_theway.jpeg',
            }
            
            products_data["products"][produto.json_key] = {
                "id": str(produto.id),
                "title": produto.nome,
                "price": float(produto.preco),
                "preco_custo": float(produto.preco_custo),
                "image": image_map.get(produto.json_key, f"./img/camisetas/{produto.json_key}.jpeg"),
                "sizes": sizes
            }
            
            # Adicionar campos extras se existirem no JSON original
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            json_path = os.path.join(base_dir, 'web', 'products.json')
            
            # Fallback para estrutura Railway
            if not os.path.exists(json_path):
                json_path = '/app/web/products.json'
                
            # Fallback para desenvolvimento local  
            if not os.path.exists(json_path):
                json_path = os.path.join(os.getcwd(), 'web', 'products.json')
            
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    original_data = json.load(f)
                    original_product = original_data.get('products', {}).get(produto.json_key, {})
                    
                    # Preservar campos extras
                    if 'images' in original_product:
                        products_data["products"][produto.json_key]['images'] = original_product['images']
                    if 'video' in original_product:
                        products_data["products"][produto.json_key]['video'] = original_product['video']
                    
                    # Preservar stripe_link dos tamanhos
                    for tamanho, tamanho_data in original_product.get('sizes', {}).items():
                        if tamanho in sizes and 'stripe_link' in tamanho_data:
                            sizes[tamanho]['stripe_link'] = tamanho_data['stripe_link']
                            sizes[tamanho]['id_stripe'] = tamanho_data.get('id_stripe', sizes[tamanho]['id_stripe'])
        
        # Salvar o arquivo
        # Tentar primeiro na estrutura local
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        output_path = os.path.join(base_dir, 'web', 'products_generated.json')
        
        # Se não existir, tentar Railway
        if not os.path.exists(os.path.dirname(output_path)):
            railway_web_path = '/app/web'
            if os.path.exists(railway_web_path):
                output_path = os.path.join(railway_web_path, 'products_generated.json')
            else:
                # Fallback para diretório temporário
                import tempfile
                temp_dir = tempfile.gettempdir()
                output_path = os.path.join(temp_dir, 'products_generated.json')
        
        # Debug: mostrar caminhos testados
        self.stdout.write(f'  🔍 Tentando salvar em: {output_path}')
        
        # Garantir que o diretório existe
        dir_path = os.path.dirname(output_path)
        self.stdout.write(f'  🔍 Diretório de destino: {dir_path}')
        
        try:
            os.makedirs(dir_path, exist_ok=True)
            self.stdout.write(f'  ✅ Diretório criado/verificado')
        except Exception as e:
            self.stdout.write(f'  ❌ Erro ao criar diretório: {str(e)}')
            raise
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(products_data, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(
            self.style.SUCCESS(f'  ✅ Arquivo gerado em: {output_path}')
        )
        self.stdout.write(
            self.style.WARNING('  ⚠️  Revise o arquivo antes de substituir o products.json original')
        )