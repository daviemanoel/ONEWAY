#!/usr/bin/env python
"""
Script para testar criação de pedido PayPal via Django API
"""
import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oneway_admin.settings')
sys.path.append('/Users/davisilva/projetos/oneway/ONEWAY/api')

# Configurar para usar SQLite local
os.environ['DATABASE_URL'] = 'sqlite:///db.sqlite3'

django.setup()

from pedidos.models import Comprador, Pedido
from django.db import connection

def test_paypal_pedido():
    """Testa criação de pedido PayPal"""
    
    print("🔍 Testando criação de pedido PayPal...")
    
    # Verificar se tabelas existem
    tables = connection.introspection.table_names()
    print(f"📊 Tabelas disponíveis: {tables}")
    
    try:
        # Criar ou buscar comprador
        comprador, created = Comprador.objects.get_or_create(
            email='teste@paypal.com',
            defaults={
                'nome': 'Cliente PayPal Teste',
                'telefone': '(11) 99999-9999'
            }
        )
        
        if created:
            print(f"✅ Comprador criado: {comprador.nome}")
        else:
            print(f"👤 Comprador existente: {comprador.nome}")
        
        # Criar pedido PayPal
        pedido = Pedido.objects.create(
            comprador=comprador,
            produto='camiseta-marrom',
            tamanho='M',
            preco=120.00,
            forma_pagamento='paypal',
            external_reference='PAYPAL-TEST-' + datetime.now().strftime('%Y%m%d%H%M%S'),
            status_pagamento='pending',
            preference_id='72409596JJ834925J',  # Order ID do teste
            observacoes='Pedido de teste PayPal'
        )
        
        print(f"✅ Pedido PayPal criado com sucesso!")
        print(f"📋 ID: {pedido.id}")
        print(f"🛒 Produto: {pedido.get_produto_display()}")
        print(f"👕 Tamanho: {pedido.tamanho}")
        print(f"💰 Preço: R$ {pedido.preco:.2f}")
        print(f"🅿️ Forma de pagamento: {pedido.get_forma_pagamento_display()}")
        print(f"📞 External Reference: {pedido.external_reference}")
        print(f"🎯 Status: {pedido.status_display}")
        
        # Verificar se PayPal está nas opções
        print(f"\n📋 Formas de pagamento disponíveis:")
        for key, value in Pedido.FORMA_PAGAMENTO_CHOICES:
            icon = "🅿️" if key == 'paypal' else "💳"
            print(f"  {icon} {key}: {value}")
        
        # Contar pedidos por forma de pagamento
        print(f"\n📊 Estatísticas de pedidos:")
        for forma, nome in Pedido.FORMA_PAGAMENTO_CHOICES:
            count = Pedido.objects.filter(forma_pagamento=forma).count()
            if count > 0:
                print(f"  {nome}: {count} pedidos")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar pedido PayPal: {e}")
        return False

if __name__ == '__main__':
    success = test_paypal_pedido()
    
    if success:
        print(f"\n🎯 TESTE CONCLUÍDO: Django suporta PayPal!")
        print(f"✅ Issue #42 completada com sucesso")
        print(f"📋 Próximo passo: Implementar endpoints Node.js (Issue #40)")
    else:
        print(f"\n💥 TESTE FALHOU: Verificar configuração Django")
    
    sys.exit(0 if success else 1)