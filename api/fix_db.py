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
        
        # Verifica se as tabelas foram criadas
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'django_%'
            """)
            tables = cursor.fetchall()
            
        if tables:
            print(f"✅ Encontradas {len(tables)} tabelas Django:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("❌ Nenhuma tabela Django encontrada")
            
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