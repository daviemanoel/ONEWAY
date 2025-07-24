from django.core.management.base import BaseCommand
from django.db import transaction
from pedidos.models import Pedido, ItemPedido, MovimentacaoEstoque, ProdutoTamanho


class Command(BaseCommand):
    help = 'Testa criação de movimentações para pedido com múltiplos itens'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'pedido_id',
            type=int,
            help='ID do pedido a testar'
        )
        parser.add_argument(
            '--forcar',
            action='store_true',
            help='Forçar recriação das movimentações (cuidado!)'
        )
    
    def handle(self, *args, **options):
        pedido_id = options['pedido_id']
        forcar = options.get('forcar', False)
        
        try:
            pedido = Pedido.objects.get(id=pedido_id)
            
            self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
            self.stdout.write(self.style.SUCCESS(f'TESTE DE MOVIMENTAÇÕES - PEDIDO #{pedido_id}'))
            self.stdout.write(self.style.SUCCESS(f'{"="*60}\n'))
            
            # Contar movimentações existentes
            movimentacoes_antes = MovimentacaoEstoque.objects.filter(pedido=pedido).count()
            self.stdout.write(f'📊 Movimentações existentes: {movimentacoes_antes}')
            
            if not pedido.itens.exists():
                self.stdout.write(self.style.ERROR('❌ Pedido não tem itens (ItemPedido)'))
                return
            
            self.stdout.write(f'\n📦 ITENS DO PEDIDO:')
            self.stdout.write(f'   Total: {pedido.itens.count()} itens')
            
            # Listar itens
            for i, item in enumerate(pedido.itens.all(), 1):
                self.stdout.write(f'\n   Item {i}:')
                self.stdout.write(f'     Produto: {item.get_produto_display()} ({item.tamanho})')
                self.stdout.write(f'     Quantidade: {item.quantidade}')
                self.stdout.write(f'     ProdutoTamanho: {item.produto_tamanho}')
                
                # Verificar movimentações específicas deste item
                if item.produto_tamanho:
                    movs = MovimentacaoEstoque.objects.filter(
                        produto_tamanho=item.produto_tamanho,
                        pedido=pedido
                    )
                    self.stdout.write(f'     Movimentações deste item: {movs.count()}')
            
            if forcar and not pedido.estoque_decrementado:
                self.stdout.write(self.style.WARNING('\n⚠️  MODO FORÇAR ATIVADO - Criando movimentações...'))
                
                with transaction.atomic():
                    for i, item in enumerate(pedido.itens.all(), 1):
                        if item.produto_tamanho and item.produto_tamanho.estoque >= item.quantidade:
                            self.stdout.write(f'\n   🔄 Processando item {i}...')
                            
                            # Criar movimentação manualmente para debug
                            mov = MovimentacaoEstoque.registrar_movimentacao(
                                produto_tamanho=item.produto_tamanho,
                                tipo='saida',
                                quantidade=item.quantidade,
                                pedido=pedido,
                                usuario='teste_manual',
                                observacao=f'TESTE - Pedido #{pedido.id} - Item {i}: {item.get_produto_display()} ({item.tamanho}) x{item.quantidade}',
                                origem='testar_movimentacoes'
                            )
                            
                            self.stdout.write(f'     ✅ Movimentação criada: ID #{mov.id}')
                            self.stdout.write(f'     Produto: {mov.produto_tamanho}')
                            self.stdout.write(f'     Quantidade: {mov.quantidade}')
                            self.stdout.write(f'     Estoque: {mov.estoque_anterior} → {mov.estoque_posterior}')
                        else:
                            self.stdout.write(f'   ❌ Item {i} sem estoque suficiente')
            
            # Recontar movimentações
            movimentacoes_depois = MovimentacaoEstoque.objects.filter(pedido=pedido).count()
            self.stdout.write(f'\n📊 RESULTADO:')
            self.stdout.write(f'   Movimentações antes: {movimentacoes_antes}')
            self.stdout.write(f'   Movimentações depois: {movimentacoes_depois}')
            self.stdout.write(f'   Diferença: +{movimentacoes_depois - movimentacoes_antes}')
            
            # Listar todas as movimentações
            self.stdout.write(f'\n🔍 TODAS AS MOVIMENTAÇÕES DO PEDIDO #{pedido_id}:')
            todas_movs = MovimentacaoEstoque.objects.filter(pedido=pedido).order_by('id')
            
            for mov in todas_movs:
                self.stdout.write(f'   #{mov.id} | {mov.produto_tamanho} | Qtd: {mov.quantidade} | {mov.data_movimentacao.strftime("%H:%M:%S")}')
            
            self.stdout.write(self.style.SUCCESS(f'\n{"="*60}\n'))
            
        except Pedido.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Pedido #{pedido_id} não encontrado'))