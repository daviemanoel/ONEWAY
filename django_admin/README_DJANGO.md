# ONE WAY 2025 - Sistema Admin Django

Sistema administrativo em Django para gestão de pedidos do evento ONE WAY 2025.

## ✅ Status da Implementação

### Funcionalidades Concluídas
- ✅ Projeto Django configurado com apps e dependências
- ✅ Modelos `Comprador` e `Pedido` implementados
- ✅ Django Admin personalizado com filtros, buscas e actions
- ✅ Banco de dados SQLite configurado com migrações
- ✅ Superuser criado (admin/admin123)
- ✅ CORS configurado para comunicação com frontend
- ✅ Dados de exemplo carregados (3 compradores, 4 pedidos)

### Próximas Etapas (Issues #13-#15)
- 🔄 API REST para comunicação Node.js ↔ Django
- 🔄 Formulário de captura de dados do comprador
- 🔄 Webhook Mercado Pago automático

## 🚀 Como Usar

### Iniciar o Sistema
```bash
cd django_admin
source venv/bin/activate
python manage.py runserver
```

### Acessar Admin
- **URL**: http://127.0.0.1:8000/admin/
- **Login**: admin
- **Senha**: admin123

## 📊 Funcionalidades do Admin

### Gestão de Compradores
- Lista com nome, email, telefone e data de cadastro
- Filtro por data de cadastro
- Busca por nome, email ou telefone
- Link direto para pedidos do comprador

### Gestão de Pedidos
- **Visualização**: ID, comprador, produto, tamanho, preço final, forma de pagamento, status
- **Filtros**: Status, produto, tamanho, forma de pagamento, data
- **Buscas**: Nome/email do comprador, external_reference, payment_id
- **Actions em lote**: 
  - 🔄 Consultar status no Mercado Pago
  - ✅ Marcar como aprovado
  - 🚫 Marcar como cancelado
- **Campos especiais**:
  - Preço com desconto PIX automaticamente calculado
  - Status com cores e emojis para fácil identificação
  - Link direto para pagamento no painel Mercado Pago

### Dados Mercado Pago
- **external_reference**: Referência única do pedido
- **payment_id**: ID do pagamento no MP
- **preference_id**: ID da preferência utilizada
- **merchant_order_id**: ID da ordem do comerciante
- **Status**: pending, approved, in_process, rejected, cancelled, refunded

## 🎯 Modelos Implementados

### Comprador
```python
- nome: CharField(100)
- email: EmailField (único por prática)
- telefone: CharField(20)
- data_cadastro: DateTimeField (auto)
```

### Pedido
```python
- comprador: ForeignKey(Comprador)
- produto: CharField(choices=PRODUTOS_CHOICES)
- tamanho: CharField(choices=['P','M','G','GG'])
- preco: DecimalField
- forma_pagamento: CharField(choices=PAGAMENTO_CHOICES)
- external_reference: CharField(unique=True)
- payment_id: CharField (MP)
- preference_id: CharField (MP)
- merchant_order_id: CharField (MP)
- status_pagamento: CharField(choices=STATUS_CHOICES)
- data_pedido: DateTimeField (auto)
- data_atualizacao: DateTimeField (auto)
- observacoes: TextField
```

## 📦 Dependências
- Django 5.2.4
- djangorestframework 3.16.0
- django-cors-headers 4.7.0
- requests 2.32.4

## 🔧 Configurações Importantes

### CORS
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://oneway-production.up.railway.app",
]
```

### Localização
- **Idioma**: Português brasileiro (pt-br)
- **Timezone**: America/Sao_Paulo
- **Admin**: Títulos e labels em português

### Banco de Dados
- **Desenvolvimento**: SQLite (db.sqlite3)
- **Produção**: Configurar PostgreSQL/MySQL via environment

## 🔗 Integração Futura

Este sistema servirá como base para:
1. **Issue #13**: API REST para receber dados do site Node.js
2. **Issue #14**: Formulário de captura de dados do comprador
3. **Issue #15**: Webhook automático do Mercado Pago

## 📝 Dados de Exemplo

O sistema já vem com dados de teste:
- **João Silva**: 2 pedidos (1 PIX aprovado, 1 PIX processando)
- **Maria Santos**: 1 pedido (cartão 2x pendente)
- **Pedro Oliveira**: 1 pedido (cartão 4x aprovado)

Todos os produtos das 4 camisetas estão representados nos dados de exemplo.