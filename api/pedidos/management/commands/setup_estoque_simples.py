from django.core.management.base import BaseCommand
from django.db import transaction
from pedidos.models import Produto, ProdutoTamanho, Pedido


class Command(BaseCommand):
    help = 'Setup simplificado - cria produtos diretamente sem arquivos'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('🚀 SETUP SIMPLIFICADO DO SISTEMA DE ESTOQUE'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        # Dados dos produtos hardcoded (do products.json)
        produtos_data = {
            'camiseta-marrom': {
                'nome': 'Camiseta One Way Marrom',
                'preco': 120.00,
                'preco_custo': 53.50,
                'ordem': 1,
                'tamanhos': {
                    'P': {'estoque': 8, 'disponivel': True},
                    'M': {'estoque': 17, 'disponivel': True},
                    'G': {'estoque': 17, 'disponivel': True},
                    'GG': {'estoque': 8, 'disponivel': True},
                }
            },
            'camiseta-jesus': {
                'nome': 'Camiseta Jesus',
                'preco': 120.00,
                'preco_custo': 55.00,
                'ordem': 2,
                'tamanhos': {
                    'P': {'estoque': 5, 'disponivel': True},
                    'M': {'estoque': 10, 'disponivel': True},
                    'G': {'estoque': 10, 'disponivel': True},
                    'GG': {'estoque': 5, 'disponivel': True},
                }
            },
            'camiseta-oneway-branca': {
                'nome': 'Camiseta ONE WAY Off White',
                'preco': 120.00,
                'preco_custo': 51.50,
                'ordem': 3,
                'tamanhos': {
                    'P': {'estoque': 5, 'disponivel': True},
                    'M': {'estoque': 10, 'disponivel': True},
                    'G': {'estoque': 10, 'disponivel': True},
                    'GG': {'estoque': 5, 'disponivel': True},
                }
            },
            'camiseta-the-way': {
                'nome': 'Camiseta The Way',
                'preco': 120.00,
                'preco_custo': 49.50,
                'ordem': 4,
                'tamanhos': {
                    'P': {'estoque': 5, 'disponivel': True},
                    'M': {'estoque': 10, 'disponivel': True},
                    'G': {'estoque': 10, 'disponivel': True},
                    'GG': {'estoque': 5, 'disponivel': True},
                }
            }
        }
        
        try:
            with transaction.atomic():
                produtos_criados = 0
                tamanhos_criados = 0
                
                # Verificar se produtos já existem
                if Produto.objects.exists():
                    self.stdout.write(self.style.WARNING('♻️  Produtos já existem - pulando criação'))
                else:
                    self.stdout.write(self.style.NOTICE('📦 Criando produtos...'))
                    
                    # Criar produtos
                    for json_key, dados in produtos_data.items():
                        produto, criado = Produto.objects.get_or_create(
                            json_key=json_key,
                            defaults={
                                'nome': dados['nome'],
                                'slug': json_key,
                                'preco': dados['preco'],
                                'preco_custo': dados['preco_custo'],
                                'ativo': True,
                                'ordem': dados['ordem'],
                            }
                        )
                        
                        if criado:
                            produtos_criados += 1
                            self.stdout.write(f"  ✅ {dados['nome']}")
                        
                        # Criar tamanhos
                        for tamanho, config in dados['tamanhos'].items():
                            tamanho_obj, criado = ProdutoTamanho.objects.get_or_create(
                                produto=produto,
                                tamanho=tamanho,
                                defaults={
                                    'estoque': config['estoque'],
                                    'disponivel': config['disponivel'],
                                }
                            )
                            
                            if criado:
                                tamanhos_criados += 1
                                self.stdout.write(f"    • {tamanho}: {config['estoque']} unidades")
                
                # Associar pedidos legacy
                pedidos_legacy = Pedido.objects.filter(produto_tamanho__isnull=True)
                associados = 0
                
                if pedidos_legacy.exists():
                    self.stdout.write(self.style.NOTICE(f'\n🔗 Associando {pedidos_legacy.count()} pedidos legacy...'))
                    
                    produto_map = {
                        'camiseta-marrom': 'camiseta-marrom',
                        'camiseta-jesus': 'camiseta-jesus', 
                        'camiseta-oneway-branca': 'camiseta-oneway-branca',
                        'camiseta-the-way': 'camiseta-the-way',
                    }
                    
                    for pedido in pedidos_legacy:
                        json_key = produto_map.get(pedido.produto)
                        if json_key:
                            try:
                                produto = Produto.objects.get(json_key=json_key)
                                produto_tamanho = ProdutoTamanho.objects.get(
                                    produto=produto,
                                    tamanho=pedido.tamanho
                                )
                                pedido.produto_tamanho = produto_tamanho
                                pedido.save()
                                associados += 1
                            except (Produto.DoesNotExist, ProdutoTamanho.DoesNotExist):
                                pass
                
                # Sincronizar estoque
                pedidos_aprovados = Pedido.objects.filter(
                    status_pagamento='approved',
                    estoque_decrementado=False,
                    produto_tamanho__isnull=False
                )
                
                processados = 0
                if pedidos_aprovados.exists():
                    self.stdout.write(self.style.NOTICE(f'\n📦 Sincronizando estoque de {pedidos_aprovados.count()} pedidos...'))
                    
                    for pedido in pedidos_aprovados:
                        if pedido.produto_tamanho.estoque > 0:
                            pedido.produto_tamanho.decrementar_estoque(1)
                            pedido.estoque_decrementado = True
                            pedido.save()
                            processados += 1
                
                # Estatísticas finais
                total_produtos = Produto.objects.count()
                total_tamanhos = ProdutoTamanho.objects.count()
                total_estoque = sum(pt.estoque for pt in ProdutoTamanho.objects.all())
                
                self.stdout.write(self.style.SUCCESS('\n' + '='*60))
                self.stdout.write(self.style.SUCCESS('✅ SETUP CONCLUÍDO COM SUCESSO!'))
                self.stdout.write(self.style.SUCCESS('='*60))
                
                self.stdout.write(self.style.SUCCESS(f'\n📊 RESUMO:'))
                self.stdout.write(f'   • Produtos criados: {produtos_criados}')
                self.stdout.write(f'   • Tamanhos criados: {tamanhos_criados}')
                self.stdout.write(f'   • Pedidos associados: {associados}')
                self.stdout.write(f'   • Estoque sincronizado: {processados}')
                
                self.stdout.write(self.style.SUCCESS(f'\n📈 TOTAIS:'))
                self.stdout.write(f'   • Total produtos: {total_produtos}')
                self.stdout.write(f'   • Total tamanhos: {total_tamanhos}')
                self.stdout.write(f'   • Total estoque: {total_estoque} unidades')
                
                self.stdout.write(self.style.SUCCESS('\n🎉 SISTEMA DE ESTOQUE OPERACIONAL!'))
                self.stdout.write(self.style.SUCCESS('Acesse o Django Admin para gerenciar produtos.'))
                self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Erro durante setup: {str(e)}'))
            raise