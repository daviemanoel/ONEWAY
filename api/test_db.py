#!/usr/bin/env python
"""
Script de teste para verificar conexão do Django com PostgreSQL
Útil para debug de problemas de deploy no Railway
"""
import os
import sys
import django
from django.db import connection
from django.core.management import execute_from_command_line

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configura as settings do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oneway_admin.settings')

print("=" * 50)
print("TESTE DE CONEXÃO DJANGO + POSTGRESQL")
print("=" * 50)

try:
    # Inicializa o Django
    print("\n1. Inicializando Django...")
    django.setup()
    print("✅ Django inicializado com sucesso")
    
    # Testa conexão com o banco
    print("\n2. Testando conexão com o banco de dados...")
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"✅ Conexão estabelecida! Resultado: {result}")
        
        # Informações sobre a conexão
        cursor.execute("SELECT current_database(), current_user, version()")
        db_info = cursor.fetchone()
        print(f"\n📊 Informações do Banco:")
        print(f"   - Database: {db_info[0]}")
        print(f"   - Usuário: {db_info[1]}")
        print(f"   - Versão PostgreSQL: {db_info[2].split(',')[0]}")
    
    # Testa migrations
    print("\n3. Verificando status das migrations...")
    from django.core.management import call_command
    from io import StringIO
    
    out = StringIO()
    call_command('showmigrations', '--plan', stdout=out)
    migrations_output = out.getvalue()
    
    if migrations_output:
        print("✅ Django consegue acessar as migrations")
        # Mostra apenas as primeiras linhas
        lines = migrations_output.split('\n')[:10]
        for line in lines:
            print(f"   {line}")
        if len(migrations_output.split('\n')) > 10:
            print("   ...")
    
    # Verifica tabelas existentes
    print("\n4. Verificando tabelas no banco...")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"✅ Encontradas {len(tables)} tabelas:")
            for table in tables[:10]:  # Mostra apenas as 10 primeiras
                print(f"   - {table[0]}")
            if len(tables) > 10:
                print(f"   ... e mais {len(tables) - 10} tabelas")
        else:
            print("⚠️  Nenhuma tabela encontrada (banco vazio)")
    
    print("\n" + "=" * 50)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("=" * 50)
    
except Exception as e:
    print("\n" + "=" * 50)
    print("❌ ERRO NA CONEXÃO!")
    print("=" * 50)
    print(f"\nTipo do erro: {type(e).__name__}")
    print(f"Mensagem: {str(e)}")
    
    # Informações de debug
    print("\n🔍 Informações de Debug:")
    
    # Variáveis de ambiente relacionadas ao banco
    db_vars = ['DATABASE_URL', 'PGDATABASE', 'PGHOST', 'PGPORT', 'PGUSER']
    print("\nVariáveis de ambiente do banco:")
    for var in db_vars:
        value = os.environ.get(var, 'NÃO DEFINIDA')
        if value != 'NÃO DEFINIDA' and var in ['DATABASE_URL', 'PGUSER']:
            # Oculta informações sensíveis
            value = value[:20] + '...' if len(value) > 20 else value
        print(f"   {var}: {value}")
    
    # Settings do Django
    try:
        from django.conf import settings
        print("\nConfiguração DATABASES do Django:")
        if hasattr(settings, 'DATABASES'):
            default_db = settings.DATABASES.get('default', {})
            print(f"   ENGINE: {default_db.get('ENGINE', 'NÃO DEFINIDO')}")
            print(f"   NAME: {default_db.get('NAME', 'NÃO DEFINIDO')}")
            print(f"   HOST: {default_db.get('HOST', 'NÃO DEFINIDO')}")
            print(f"   PORT: {default_db.get('PORT', 'NÃO DEFINIDO')}")
            print(f"   USER: {default_db.get('USER', 'NÃO DEFINIDO')[:10]}..." if default_db.get('USER') else "   USER: NÃO DEFINIDO")
    except:
        print("   ❌ Não foi possível acessar as configurações do Django")
    
    print("\n💡 Dicas para resolver:")
    print("   1. Verifique se DATABASE_URL está configurada no Railway")
    print("   2. Certifique-se que o PostgreSQL está provisionado")
    print("   3. Verifique se dj_database_url está instalado")
    print("   4. Confirme que settings.py está usando dj_database_url.parse()")
    
    sys.exit(1)