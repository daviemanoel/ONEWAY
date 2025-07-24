from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Setup completo do sistema de estoque - roda automaticamente no deploy'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('🚀 SETUP AUTOMÁTICO DO SISTEMA DE ESTOQUE'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        try:
            # 1. Migrar produtos do JSON
            self.stdout.write(self.style.NOTICE('1. Migrando produtos do products.json...'))
            call_command('migrar_produtos')
            
            # 2. Associar pedidos legacy
            self.stdout.write(self.style.NOTICE('\n2. Associando pedidos legacy...'))
            call_command('associar_pedidos_legacy')
            
            # 3. Sincronizar estoque inicial
            self.stdout.write(self.style.NOTICE('\n3. Sincronizando estoque...'))
            call_command('sincronizar_estoque', '--gerar-json')
            
            self.stdout.write(self.style.SUCCESS('\n' + '='*60))
            self.stdout.write(self.style.SUCCESS('✅ SETUP CONCLUÍDO COM SUCESSO!'))
            self.stdout.write(self.style.SUCCESS('Sistema de estoque está pronto para uso.'))
            self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Erro durante setup: {str(e)}'))
            raise