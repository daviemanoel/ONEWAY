#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oneway_admin.settings')
django.setup()

from django.contrib.auth.models import User
from pedidos.models import Comprador, Pedido
from decimal import Decimal

def criar_superuser():
    """Criar superuser se não existir"""
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@oneway.com', 'admin123')
        print("✅ Superuser 'admin' criado com sucesso!")
        print("   Username: admin")
        print("   Password: admin123")
    else:
        print("ℹ️  Superuser 'admin' já existe")

def criar_dados_exemplo():
    """Criar dados de exemplo para testes"""
    
    # Criar compradores de exemplo
    comprador1, created = Comprador.objects.get_or_create(
        email="joao@email.com",
        defaults={
            'nome': "João Silva",
            'telefone': "(11) 99999-1234"
        }
    )
    
    comprador2, created = Comprador.objects.get_or_create(
        email="maria@email.com",
        defaults={
            'nome': "Maria Santos",
            'telefone': "(11) 88888-5678"
        }
    )
    
    comprador3, created = Comprador.objects.get_or_create(
        email="pedro@email.com",
        defaults={
            'nome': "Pedro Oliveira",
            'telefone': "(11) 77777-9012"
        }
    )
    
    print(f"✅ Compradores criados: {Comprador.objects.count()}")
    
    # Criar pedidos de exemplo
    pedidos_exemplo = [
        {
            'comprador': comprador1,
            'produto': 'camiseta-marrom',
            'tamanho': 'M',
            'preco': Decimal('120.00'),
            'forma_pagamento': 'pix',
            'external_reference': 'ONEWAY-001-20250714120000',
            'payment_id': '123456789',
            'status_pagamento': 'approved'
        },
        {
            'comprador': comprador2,
            'produto': 'camiseta-jesus',
            'tamanho': 'G',
            'preco': Decimal('120.00'),
            'forma_pagamento': '2x',
            'external_reference': 'ONEWAY-002-20250714120100',
            'payment_id': '987654321',
            'status_pagamento': 'pending'
        },
        {
            'comprador': comprador3,
            'produto': 'camiseta-oneway-branca',
            'tamanho': 'P',
            'preco': Decimal('120.00'),
            'forma_pagamento': '4x',
            'external_reference': 'ONEWAY-003-20250714120200',
            'payment_id': '456789123',
            'status_pagamento': 'approved'
        },
        {
            'comprador': comprador1,
            'produto': 'camiseta-the-way',
            'tamanho': 'GG',
            'preco': Decimal('120.00'),
            'forma_pagamento': 'pix',
            'external_reference': 'ONEWAY-004-20250714120300',
            'payment_id': '789123456',
            'status_pagamento': 'in_process'
        }
    ]
    
    for pedido_data in pedidos_exemplo:
        pedido, created = Pedido.objects.get_or_create(
            external_reference=pedido_data['external_reference'],
            defaults=pedido_data
        )
        if created:
            print(f"✅ Pedido criado: {pedido}")
    
    print(f"✅ Total de pedidos: {Pedido.objects.count()}")

if __name__ == '__main__':
    print("🚀 Iniciando criação de dados do ONE WAY Admin...")
    print()
    
    try:
        criar_superuser()
        print()
        criar_dados_exemplo()
        print()
        print("🎉 Sistema configurado com sucesso!")
        print()
        print("Para acessar o admin:")
        print("1. Execute: python manage.py runserver")
        print("2. Acesse: http://127.0.0.1:8000/admin/")
        print("3. Login: admin / admin123")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)