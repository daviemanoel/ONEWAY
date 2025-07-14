#!/usr/bin/env python
import os
import django
from django.core.management import execute_from_command_line
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oneway_admin.settings')
django.setup()

def init_database():
    """Inicializa o banco de dados apenas se necessário"""
    
    try:
        # Tenta verificar se as tabelas existem
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='django_session';")
            result = cursor.fetchone()
            
        if result:
            print("✅ Banco já possui tabelas Django - pulando inicialização")
            return
            
    except Exception as e:
        print(f"🔄 Erro ao verificar tabelas, iniciando criação: {e}")
    
    print("🔄 Criando tabelas Django...")
    
    # Executar migrações
    execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
    
    print("✅ Tabelas Django criadas com sucesso")

if __name__ == "__main__":
    init_database()