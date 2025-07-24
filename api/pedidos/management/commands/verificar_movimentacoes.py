from django.core.management.base import BaseCommand
from pedidos.models import Pedido, ItemPedido, MovimentacaoEstoque


class Command(BaseCommand):
    help = 'Verifica movimentações de estoque de um pedido específico'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'pedido_id',
            type=int,
            help='ID do pedido a verificar'
        )
    
    def handle(self, *args, **options):
        pedido_id = options['pedido_id']
        
        try:
            pedido = Pedido.objects.get(id=pedido_id)
            
            self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
            self.stdout.write(self.style.SUCCESS(f'ANÁLISE DE MOVIMENTAÇÕES - PEDIDO #{pedido_id}'))
            self.stdout.write(self.style.SUCCESS(f'{"="*60}\n'))
            
            # Informações do pedido
            self.stdout.write(f'📋 INFORMAÇÕES DO PEDIDO:')
            self.stdout.write(f'   Comprador: {pedido.comprador.nome}')
            self.stdout.write(f'   Status: {pedido.get_status_pagamento_display()}')
            self.stdout.write(f'   Forma de pagamento: {pedido.get_forma_pagamento_display()}')
            self.stdout.write(f'   Estoque decrementado: {"✅ Sim" if pedido.estoque_decrementado else "❌ Não"}')
            
            # Verificar se tem itens
            if pedido.itens.exists():
                self.stdout.write(f'\n📦 ITENS DO PEDIDO:')
                self.stdout.write(f'   Total de itens: {pedido.itens.count()}')
                
                for i, item in enumerate(pedido.itens.all(), 1):
                    self.stdout.write(f'\n   Item {i}:')
                    self.stdout.write(f'     Produto: {item.get_produto_display()}')
                    self.stdout.write(f'     Tamanho: {item.tamanho}')
                    self.stdout.write(f'     Quantidade: {item.quantidade}')
                    self.stdout.write(f'     ProdutoTamanho: {item.produto_tamanho or "❌ Não associado"}')
                    
                    # Buscar movimentações deste item específico
                    if item.produto_tamanho:
                        movimentacoes = MovimentacaoEstoque.objects.filter(
                            produto_tamanho=item.produto_tamanho,
                            pedido=pedido
                        ).order_by('data_movimentacao')
                        
                        if movimentacoes.exists():
                            self.stdout.write(f'     📊 Movimentações encontradas: {movimentacoes.count()}')
                            for mov in movimentacoes:
                                self.stdout.write(f'       - {mov.data_movimentacao.strftime("%d/%m %H:%M")} | '
                                                f'Qtd: {mov.quantidade} | '
                                                f'Estoque: {mov.estoque_anterior} → {mov.estoque_posterior}')
                        else:
                            self.stdout.write(f'     ❌ Nenhuma movimentação encontrada para este item')
            else:
                # Pedido legacy
                self.stdout.write(f'\n📊 PEDIDO LEGACY (sem ItemPedido):')
                self.stdout.write(f'   Produto: {pedido.get_produto_display()}')
                self.stdout.write(f'   Tamanho: {pedido.tamanho}')
                self.stdout.write(f'   ProdutoTamanho: {pedido.produto_tamanho or "❌ Não associado"}')
            
            # Buscar TODAS as movimentações relacionadas ao pedido
            self.stdout.write(f'\n🔍 TODAS AS MOVIMENTAÇÕES DO PEDIDO:')
            todas_movimentacoes = MovimentacaoEstoque.objects.filter(
                pedido=pedido
            ).select_related('produto_tamanho__produto').order_by('data_movimentacao')
            
            if todas_movimentacoes.exists():
                self.stdout.write(f'   Total: {todas_movimentacoes.count()} movimentações')
                for mov in todas_movimentacoes:
                    self.stdout.write(f'   - {mov.produto_tamanho} | '
                                    f'Qtd: {mov.quantidade} | '
                                    f'{mov.data_movimentacao.strftime("%d/%m/%Y %H:%M:%S")}')
                    self.stdout.write(f'     Observação: {mov.observacao}')
            else:
                self.stdout.write(f'   ❌ Nenhuma movimentação encontrada para este pedido')
            
            self.stdout.write(self.style.SUCCESS(f'\n{"="*60}\n'))
            
        except Pedido.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Pedido #{pedido_id} não encontrado'))