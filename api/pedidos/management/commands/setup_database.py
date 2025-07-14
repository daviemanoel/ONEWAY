from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction, connection
import time

class Command(BaseCommand):
    help = 'Setup database tables for Railway'

    def handle(self, *args, **options):
        self.stdout.write("🔄 Configurando banco PostgreSQL...")
        
        try:
            # Força reconexão limpa
            connection.close()
            time.sleep(1)
            
            with transaction.atomic():
                # Migra todas as apps do Django primeiro
                call_command('migrate', 'contenttypes', verbosity=0)
                call_command('migrate', 'auth', verbosity=0)
                call_command('migrate', 'sessions', verbosity=0)
                call_command('migrate', 'admin', verbosity=0)
                call_command('migrate', 'authtoken', verbosity=0)
                
                # Depois migra nossa app
                call_command('migrate', 'pedidos', verbosity=0)
                
            self.stdout.write("✅ Todas as tabelas criadas com sucesso!")
            
        except Exception as e:
            self.stdout.write(f"❌ Erro: {e}")
            # Fallback
            try:
                call_command('migrate', '--run-syncdb', verbosity=1)
                self.stdout.write("✅ Fallback executado com sucesso!")
            except Exception as e2:
                self.stdout.write(f"❌ Fallback falhou: {e2}")
                raise