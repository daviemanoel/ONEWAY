#!/usr/bin/env python
import os
import django
from django.core.management import execute_from_command_line
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oneway_admin.settings')
django.setup()

def fix_database():
    """Força criação de todas as tabelas Django"""
    
    print("🔄 Verificando e criando tabelas no PostgreSQL...")
    
    try:
        # Primeiro, força a criação do schema
        from django.core.management.commands.migrate import Command as MigrateCommand
        from django.db import transaction
        
        with transaction.atomic():
            # Executa migrate com syncdb para criar tabelas
            execute_from_command_line(['manage.py', 'migrate', '--run-syncdb', '--verbosity=2'])
            
        print("✅ Tabelas criadas com sucesso!")
        
        print("✅ Migrações executadas com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        # Tenta uma abordagem mais agressiva
        try:
            print("🔄 Tentando abordagem alternativa...")
            execute_from_command_line(['manage.py', 'migrate', '--fake-initial'])
            execute_from_command_line(['manage.py', 'migrate'])
            print("✅ Migração alternativa concluída!")
        except Exception as e2:
            print(f"❌ Erro na migração alternativa: {e2}")

if __name__ == "__main__":
    fix_database()