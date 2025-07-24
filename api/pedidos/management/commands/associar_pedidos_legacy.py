from django.core.management.base import BaseCommand
from django.db import transaction
from pedidos.models import Pedido, ItemPedido, Produto, ProdutoTamanho


class Command(BaseCommand):
    help = 'Associa pedidos legacy aos novos models de Produto e ProdutoTamanho'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a associação sem salvar no banco',
        )
        parser.add_argument(
            '--pedido-id',
            type=int,
            help='Processar apenas um pedido específico',
        )
    
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        pedido_id = options.get('pedido_id')
        
        # Mapear produtos antigos para json_key
        produto_map = {
            'camiseta-marrom': 'camiseta-marrom',
            'camiseta-jesus': 'camiseta-jesus',
            'camiseta-oneway-branca': 'camiseta-oneway-branca',
            'camiseta-the-way': 'camiseta-the-way',
        }
        
        # Buscar pedidos para processar
        queryset = Pedido.objects.filter(produto_tamanho__isnull=True)
        if pedido_id:
            queryset = queryset.filter(id=pedido_id)
        
        total_pedidos = queryset.count()
        
        if total_pedidos == 0:
            self.stdout.write(self.style.WARNING('Nenhum pedido legacy encontrado para processar'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Encontrados {total_pedidos} pedidos legacy para processar'))
        
        pedidos_associados = 0
        pedidos_sem_produto = 0
        pedidos_sem_tamanho = 0
        pedidos_erro = 0
        
        itens_associados = 0
        itens_sem_produto = 0
        itens_sem_tamanho = 0
        
        try:
            with transaction.atomic():
                for pedido in queryset:
                    self.stdout.write(f"\nProcessando Pedido #{pedido.id}")
                    
                    # Obter json_key do produto
                    json_key = produto_map.get(pedido.produto)
                    
                    if not json_key:
                        self.stdout.write(self.style.ERROR(f"  ❌ Produto não mapeado: {pedido.produto}"))
                        pedidos_sem_produto += 1
                        continue
                    
                    try:
                        # Buscar produto no novo sistema
                        produto = Produto.objects.get(json_key=json_key)
                        
                        # Buscar tamanho
                        produto_tamanho = ProdutoTamanho.objects.filter(
                            produto=produto,
                            tamanho=pedido.tamanho
                        ).first()
                        
                        if not produto_tamanho:
                            self.stdout.write(self.style.ERROR(
                                f"  ❌ Tamanho {pedido.tamanho} não encontrado para {produto.nome}"
                            ))
                            pedidos_sem_tamanho += 1
                            continue
                        
                        # Associar pedido
                        pedido.produto_tamanho = produto_tamanho
                        if not dry_run:
                            pedido.save()
                        
                        self.stdout.write(self.style.SUCCESS(
                            f"  ✅ Pedido associado a: {produto_tamanho}"
                        ))
                        pedidos_associados += 1
                        
                    except Produto.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f"  ❌ Produto não encontrado: {json_key}"))
                        pedidos_sem_produto += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  ❌ Erro: {str(e)}"))
                        pedidos_erro += 1
                
                # Processar ItemPedido
                self.stdout.write('\n' + '='*50)
                self.stdout.write('Processando itens de pedido...')
                
                itens_queryset = ItemPedido.objects.filter(produto_tamanho__isnull=True)
                
                for item in itens_queryset:
                    # Obter json_key do produto
                    json_key = produto_map.get(item.produto)
                    
                    if not json_key:
                        itens_sem_produto += 1
                        continue
                    
                    try:
                        # Buscar produto no novo sistema
                        produto = Produto.objects.get(json_key=json_key)
                        
                        # Buscar tamanho
                        produto_tamanho = ProdutoTamanho.objects.filter(
                            produto=produto,
                            tamanho=item.tamanho
                        ).first()
                        
                        if not produto_tamanho:
                            itens_sem_tamanho += 1
                            continue
                        
                        # Associar item
                        item.produto_tamanho = produto_tamanho
                        if not dry_run:
                            item.save()
                        
                        itens_associados += 1
                        
                    except Produto.DoesNotExist:
                        itens_sem_produto += 1
                
                if dry_run:
                    self.stdout.write(self.style.WARNING('\n🔍 DRY RUN - Nenhuma alteração foi salva'))
                    raise Exception('Dry run - rollback')
        
        except Exception as e:
            if dry_run and str(e) == 'Dry run - rollback':
                pass
            else:
                self.stdout.write(self.style.ERROR(f'\n❌ Erro durante associação: {str(e)}'))
                raise
        
        # Resumo final
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('RESUMO DA ASSOCIAÇÃO:'))
        self.stdout.write(self.style.SUCCESS('\nPedidos:'))
        self.stdout.write(self.style.SUCCESS(f'  Associados com sucesso: {pedidos_associados}'))
        self.stdout.write(self.style.WARNING(f'  Sem produto mapeado: {pedidos_sem_produto}'))
        self.stdout.write(self.style.WARNING(f'  Sem tamanho encontrado: {pedidos_sem_tamanho}'))
        self.stdout.write(self.style.ERROR(f'  Com erro: {pedidos_erro}'))
        
        self.stdout.write(self.style.SUCCESS('\nItens de Pedido:'))
        self.stdout.write(self.style.SUCCESS(f'  Associados com sucesso: {itens_associados}'))
        self.stdout.write(self.style.WARNING(f'  Sem produto mapeado: {itens_sem_produto}'))
        self.stdout.write(self.style.WARNING(f'  Sem tamanho encontrado: {itens_sem_tamanho}'))
        self.stdout.write(self.style.SUCCESS('='*50))
        
        # Estatísticas finais
        pedidos_com_novo_sistema = Pedido.objects.filter(produto_tamanho__isnull=False).count()
        pedidos_legacy_restantes = Pedido.objects.filter(produto_tamanho__isnull=True).count()
        
        self.stdout.write(f'\nPedidos usando novo sistema: {pedidos_com_novo_sistema}')
        self.stdout.write(f'Pedidos legacy restantes: {pedidos_legacy_restantes}')
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\n✅ Associação concluída com sucesso!'))