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
            default=30,
            help='Processar pedidos dos últimos N dias (padrão: 30)',
        )
        parser.add_argument(
            '--gerar-json',
            action='store_true',
            help='Gerar products.json após sincronização',
        )
        parser.add_argument(
            '--reprocessar',
            action='store_true',
            help='Reprocessar pedidos que já tiveram estoque decrementado (CUIDADO!)',
        )
    
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        dias = options.get('dias', 30)
        gerar_json = options.get('gerar_json', False)
        reprocessar = options.get('reprocessar', False)
        
        # Data limite para processar pedidos
        data_limite = datetime.now() - timedelta(days=dias)
        
        self.stdout.write(self.style.SUCCESS(f'\n{"="*50}'))
        self.stdout.write(self.style.SUCCESS('SINCRONIZAÇÃO DE ESTOQUE'))
        self.stdout.write(self.style.SUCCESS(f'{"="*50}\n'))
        
        self.stdout.write(f'📅 Processando pedidos dos últimos {dias} dias (desde {data_limite.strftime("%d/%m/%Y %H:%M")})')
        
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
                
                from django.db.models import Q
                
                # Buscar pedidos aprovados OU pedidos presenciais (mesmo pending)
                # IMPORTANTE: Só processar aqui pedidos que NÃO têm ItemPedido (para evitar duplicação)
                query_novos = Q(status_pagamento='approved') | Q(forma_pagamento='presencial')
                query_novos &= Q(produto_tamanho__isnull=False)
                query_novos &= Q(data_pedido__gte=data_limite)
                
                if not reprocessar:
                    query_novos &= Q(estoque_decrementado=False)
                
                # Excluir pedidos que têm ItemPedido (esses vão para seção múltiplos itens)
                pedidos_com_itens_ids = Pedido.objects.filter(
                    itens__isnull=False
                ).values_list('id', flat=True).distinct()
                
                if pedidos_com_itens_ids:
                    query_novos &= ~Q(id__in=pedidos_com_itens_ids)
                
                pedidos_novos = Pedido.objects.filter(query_novos).select_related('produto_tamanho', 'comprador')
                
                self.stdout.write(f'   Encontrados: {pedidos_novos.count()} pedidos do novo sistema')
                
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
                
                # Buscar TODOS os pedidos que têm ItemPedido (independente de ter produto_tamanho ou não)
                query_multiplos = Q(status_pagamento='approved') | Q(forma_pagamento='presencial')
                query_multiplos &= Q(data_pedido__gte=data_limite)
                query_multiplos &= Q(itens__isnull=False)  # Só pedidos que TÊM ItemPedido
                
                if not reprocessar:
                    query_multiplos &= Q(estoque_decrementado=False)
                
                pedidos_multiplos = Pedido.objects.filter(query_multiplos).prefetch_related('itens__produto_tamanho').select_related('comprador').distinct()
                
                self.stdout.write(f'   Encontrados: {pedidos_multiplos.count()} candidatos a pedidos múltiplos')
                
                # Todos os pedidos da query já têm itens, então não precisa filtrar
                pedidos_com_itens = []
                for pedido in pedidos_multiplos:
                    self.stdout.write(f'   🔍 Analisando pedido #{pedido.id} com {pedido.itens.count()} itens')
                    pedidos_com_itens.append(pedido.id)
                    
                    try:
                        # Verificar se há estoque para todos os itens
                        pode_processar = True
                        itens_sem_estoque = []
                        
                        for item in pedido.itens.all():
                            # Buscar produto_tamanho se não estiver preenchido
                            produto_tamanho_obj = item.produto_tamanho
                            
                            if not produto_tamanho_obj:
                                # Tentar buscar baseado nos campos legacy
                                try:
                                    produto_obj = Produto.objects.get(json_key=item.produto)
                                    produto_tamanho_obj = produto_obj.tamanhos.get(tamanho=item.tamanho)
                                    self.stdout.write(f"     🔍 Item encontrado via legacy: {item.get_produto_display()} ({item.tamanho}) → {produto_tamanho_obj}")
                                except (Produto.DoesNotExist, ProdutoTamanho.DoesNotExist):
                                    self.stdout.write(f"     ❌ Item não encontrado: {item.get_produto_display()} ({item.tamanho})")
                                    produto_tamanho_obj = None
                            
                            if produto_tamanho_obj:
                                self.stdout.write(f"     📋 Verificando item: {item.get_produto_display()} ({item.tamanho}) x{item.quantidade}")
                                if produto_tamanho_obj.estoque < item.quantidade:
                                    pode_processar = False
                                    itens_sem_estoque.append(
                                        f"{produto_tamanho_obj} (precisa: {item.quantidade}, tem: {produto_tamanho_obj.estoque})"
                                    )
                                    self.stdout.write(f"       ❌ Estoque insuficiente: {produto_tamanho_obj.estoque} < {item.quantidade}")
                                else:
                                    self.stdout.write(f"       ✅ Estoque OK: {produto_tamanho_obj.estoque} >= {item.quantidade}")
                            else:
                                self.stdout.write(f"     ⚠️  Item sem produto_tamanho: {item.get_produto_display()} ({item.tamanho})")
                        
                        if pode_processar:
                            # Decrementar estoque de todos os itens
                            total_itens = pedido.itens.count()
                            self.stdout.write(f"     🔄 Processando {total_itens} itens do pedido #{pedido.id}...")
                            
                            # Debug: contar movimentações antes
                            from pedidos.models import MovimentacaoEstoque
                            movs_antes = MovimentacaoEstoque.objects.filter(pedido=pedido).count()
                            self.stdout.write(f"     📊 Movimentações existentes: {movs_antes}")
                            
                            itens_processados = 0
                            if not dry_run:
                                for idx, item in enumerate(pedido.itens.all(), 1):
                                    try:
                                        # Buscar produto_tamanho se não estiver preenchido
                                        produto_tamanho_obj = item.produto_tamanho
                                        
                                        if not produto_tamanho_obj:
                                            # Tentar buscar baseado nos campos legacy
                                            try:
                                                produto_obj = Produto.objects.get(json_key=item.produto)
                                                produto_tamanho_obj = produto_obj.tamanhos.get(tamanho=item.tamanho)
                                                self.stdout.write(f"       💡 Usando produto_tamanho via legacy: {produto_tamanho_obj}")
                                            except (Produto.DoesNotExist, ProdutoTamanho.DoesNotExist):
                                                produto_tamanho_obj = None
                                        
                                        if produto_tamanho_obj:
                                            self.stdout.write(f"       🔽 Item {idx}/{total_itens}: {item.get_produto_display()} ({item.tamanho}) x{item.quantidade}")
                                            
                                            # Contar movimentações antes deste item
                                            movs_item_antes = MovimentacaoEstoque.objects.filter(
                                                pedido=pedido,
                                                produto_tamanho=produto_tamanho_obj
                                            ).count()
                                            
                                            sucesso = produto_tamanho_obj.decrementar_estoque(
                                                quantidade=item.quantidade,
                                                pedido=pedido,
                                                usuario='sistema',
                                                observacao=f'Sincronização automática - Pedido #{pedido.id} - Item {idx}: {item.get_produto_display()} ({item.tamanho})',
                                                origem='sincronizar_estoque_comando'
                                            )
                                            if sucesso:
                                                # Verificar se movimentação foi criada
                                                movs_item_depois = MovimentacaoEstoque.objects.filter(
                                                    pedido=pedido,
                                                    produto_tamanho=produto_tamanho_obj
                                                ).count()
                                                nova_mov = movs_item_depois - movs_item_antes
                                                
                                                self.stdout.write(f"         ✅ Movimentação registrada - Estoque restante: {produto_tamanho_obj.estoque}")
                                                self.stdout.write(f"         📈 Movimentações criadas para este item: {nova_mov}")
                                                itens_processados += 1
                                            else:
                                                self.stdout.write(f"         ❌ Falha ao decrementar estoque")
                                        else:
                                            self.stdout.write(f"       ⚠️  Item ignorado (sem produto_tamanho): {item.get_produto_display()} ({item.tamanho})")
                                    except Exception as item_error:
                                        self.stdout.write(f"         ❌ Erro no item {item.get_produto_display()} ({item.tamanho}): {str(item_error)}")
                                
                                # Marcar pedido como processado APÓS processar todos os itens
                                if itens_processados > 0:
                                    pedido.estoque_decrementado = True
                                    pedido.save()
                                
                                # Debug: contar movimentações depois
                                movs_depois = MovimentacaoEstoque.objects.filter(pedido=pedido).count()
                                self.stdout.write(f"     📊 Total de movimentações após processamento: {movs_depois} (eram {movs_antes})")
                                self.stdout.write(f"     📊 Novas movimentações criadas: {movs_depois - movs_antes}")
                            else:
                                # Contar itens que seriam processados no dry run
                                for item in pedido.itens.all():
                                    # Buscar produto_tamanho se não estiver preenchido
                                    produto_tamanho_obj = item.produto_tamanho
                                    
                                    if not produto_tamanho_obj:
                                        try:
                                            produto_obj = Produto.objects.get(json_key=item.produto)
                                            produto_tamanho_obj = produto_obj.tamanhos.get(tamanho=item.tamanho)
                                        except (Produto.DoesNotExist, ProdutoTamanho.DoesNotExist):
                                            produto_tamanho_obj = None
                                    
                                    if produto_tamanho_obj:
                                        self.stdout.write(f"       🔽 [DRY RUN] Decrementaria: {item.get_produto_display()} ({item.tamanho}) x{item.quantidade}")
                                        itens_processados += 1
                            
                            self.stdout.write(
                                f"  ✅ Pedido #{pedido.id}: {itens_processados}/{pedido.itens.count()} itens processados com sucesso"
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
                    Q(status_pagamento='approved') | Q(forma_pagamento='presencial'),
                    estoque_decrementado=False,
                    produto_tamanho__isnull=True,
                    data_pedido__gte=data_limite
                ).exclude(id__in=pedidos_com_itens).select_related('comprador')
                
                self.stdout.write(f'   Encontrados: {pedidos_legacy.count()} pedidos legacy')
                if pedidos_legacy.exists():
                    for p in pedidos_legacy[:3]:  # Mostrar até 3 exemplos
                        self.stdout.write(f'     - Pedido #{p.id}: {p.produto} ({p.tamanho}) - {p.forma_pagamento}')
                
                for pedido in pedidos_legacy:
                    try:
                        # Buscar ProdutoTamanho baseado nos campos legacy
                        try:
                            produto = Produto.objects.get(json_key=pedido.produto)
                            produto_tamanho = produto.tamanhos.get(tamanho=pedido.tamanho)
                            
                            if produto_tamanho.estoque > 0:
                                if not dry_run:
                                    produto_tamanho.decrementar_estoque(
                                        quantidade=1,
                                        pedido=pedido,
                                        usuario='sistema',
                                        observacao=f'Sincronização legacy - Pedido #{pedido.id}',
                                        origem='sincronizar_estoque_legacy'
                                    )
                                    pedido.estoque_decrementado = True
                                    pedido.save()
                                
                                self.stdout.write(
                                    f"  ✅ Pedido legacy #{pedido.id}: {produto_tamanho} "
                                    f"(estoque: {produto_tamanho.estoque - 1})"
                                )
                                processados += 1
                            else:
                                self.stdout.write(
                                    self.style.ERROR(
                                        f"  ❌ Pedido legacy #{pedido.id}: Sem estoque para {produto_tamanho}"
                                    )
                                )
                                sem_estoque += 1
                                
                        except (Produto.DoesNotExist, ProdutoTamanho.DoesNotExist):
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  ⚠️  Pedido legacy #{pedido.id}: Produto/tamanho não encontrado "
                                    f"({pedido.produto}/{pedido.tamanho}). Execute 'associar_pedidos_legacy'."
                                )
                            )
                            
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"  ❌ Erro no pedido legacy #{pedido.id}: {str(e)}")
                        )
                        erros += 1
                
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