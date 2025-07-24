from django.core.management.base import BaseCommand
from django.core.management import call_command
from pedidos.models import Produto, Pedido


class Command(BaseCommand):
    help = 'Setup inteligente do sistema de estoque - executa apenas o necessário'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('🚀 SETUP AUTOMÁTICO DO SISTEMA DE ESTOQUE'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        try:
            # Verificar se é primeira execução
            produtos_existem = Produto.objects.exists()
            pedidos_legacy_existem = Pedido.objects.filter(produto_tamanho__isnull=True).exists()
            
            if not produtos_existem:
                # PRIMEIRA VEZ - Migração completa
                self.stdout.write(self.style.WARNING('🔄 Primeira execução detectada - fazendo setup completo...'))
                
                # 1. Migrar produtos do JSON
                self.stdout.write(self.style.NOTICE('1. Migrando produtos do products.json...'))
                call_command('migrar_produtos')
                
                # 2. Associar pedidos legacy (se existirem)
                if pedidos_legacy_existem:
                    self.stdout.write(self.style.NOTICE('2. Associando pedidos legacy...'))
                    call_command('associar_pedidos_legacy')
                else:
                    self.stdout.write(self.style.NOTICE('2. Nenhum pedido legacy encontrado - pularemos associação'))
                
                # 3. Sincronizar estoque inicial
                self.stdout.write(self.style.NOTICE('3. Sincronizando estoque inicial...'))
                call_command('sincronizar_estoque', '--gerar-json')
                
                self.stdout.write(self.style.SUCCESS('\n✅ SETUP INICIAL CONCLUÍDO!'))
                self.stdout.write(self.style.SUCCESS('Produtos criados e estoque configurado.'))
                
            else:
                # EXECUÇÕES SUBSEQUENTES - Apenas sincronização
                self.stdout.write(self.style.NOTICE('♻️  Sistema já configurado - executando apenas sincronização...'))
                
                # Verificar se há pedidos legacy pendentes
                if pedidos_legacy_existem:
                    self.stdout.write(self.style.WARNING('⚠️  Pedidos legacy encontrados - associando...'))
                    call_command('associar_pedidos_legacy')
                
                # Sincronizar estoque
                self.stdout.write(self.style.NOTICE('📦 Sincronizando estoque...'))
                call_command('sincronizar_estoque', '--gerar-json')
                
                self.stdout.write(self.style.SUCCESS('✅ SINCRONIZAÇÃO CONCLUÍDA!'))
            
            # Estatísticas finais
            total_produtos = Produto.objects.count()
            total_pedidos_novo_sistema = Pedido.objects.filter(produto_tamanho__isnull=False).count()
            total_pedidos_legacy = Pedido.objects.filter(produto_tamanho__isnull=True).count()
            
            self.stdout.write(self.style.SUCCESS('\n📊 ESTATÍSTICAS:'))
            self.stdout.write(f'   Produtos cadastrados: {total_produtos}')
            self.stdout.write(f'   Pedidos no novo sistema: {total_pedidos_novo_sistema}')
            self.stdout.write(f'   Pedidos legacy restantes: {total_pedidos_legacy}')
            
            self.stdout.write(self.style.SUCCESS('\n' + '='*60))
            self.stdout.write(self.style.SUCCESS('🎉 SISTEMA DE ESTOQUE OPERACIONAL!'))
            self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Erro durante setup: {str(e)}'))
            self.stdout.write(self.style.ERROR('Verifique os logs acima para mais detalhes.'))
            raise