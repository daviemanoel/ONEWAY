# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## PRINCÍPIOS IMPORTANTES
- **SEMPRE responder em português brasileiro**
- **SEMPRE perguntar antes de gerar código** (regra obrigatória)
- Usar terminologia técnica em português quando possível
- Manter consistência com o idioma do projeto (site em português)
- Preferir soluções simples e diretas em vez de múltiplas opções

## Visão Geral do Projeto

Este é um site de e-commerce para o evento "ONE WAY 2025" (31 de julho - 2 de agosto de 2025). É uma SPA construída com HTML/CSS/JavaScript vanilla, com backend Node.js/Express para pagamentos e sistema Django para administração.

### Arquitetura do Sistema
```
[Frontend HTML/JS] → [Node.js/Express] → [Mercado Pago + PayPal APIs]
        ↓                    ↓
[products.json]    [Django REST API] → [PostgreSQL Railway]
        ↓                    ↓
[Cache 5min]       [Admin Interface] → [Gestão Completa]
```

### Status: 🚀 **PRODUÇÃO ATIVA**
- ✅ **Frontend**: https://oneway.mevamfranca.com.br
- ✅ **Admin Django**: https://api.oneway.mevamfranca.com.br/admin (admin/oneway2025)
- ✅ **Pagamentos**: Mercado Pago + PayPal configuração dinâmica
- ✅ **Banco**: PostgreSQL Railway persistente
- ✅ **Carrinho**: Sistema completo de múltiplos itens

## Comandos de Desenvolvimento

### Railway CLI (Produção)
```bash
railway logs --service WEB    # Logs Node.js em tempo real
railway logs --service API    # Logs Django em tempo real
railway status                # Status dos serviços
railway up                    # Deploy forçado
railway link                  # Conectar ao projeto ONEWAY
```

### Frontend (Estático)
```bash
# Desenvolvimento local
open web/index.html           # Abrir diretamente no navegador
cd web && python -m http.server 8000  # Servidor local porta 8000
cd web && npx serve           # Alternativa com npx serve
```

### Backend Node.js (Pagamentos)
```bash
cd web
npm install                   # Instalar dependências
npm start                     # Servidor produção porta 3000
npm run dev                   # Servidor desenvolvimento
node server.js               # Executar diretamente
```

### Django Admin (Gestão)
```bash
cd api
pip install -r requirements.txt      # Instalar dependências
python manage.py migrate            # Migrar banco local (SQLite)
python manage.py runserver          # Servidor local porta 8000
python manage.py createsuperuser    # Criar admin local

# Comandos customizados
python manage.py setup_database     # Setup automático produção
python manage.py criar_token_api    # Gerar token para Node.js
```

### Comandos de Diagnóstico
```bash
# Health checks
curl https://oneway.mevamfranca.com.br/health
curl https://oneway.mevamfranca.com.br/mp-health

# Testes locais
python api/test_db.py         # Diagnóstico banco (125 linhas)
python api/fix_db.py          # Recuperação em caso de problemas

# API REST
curl -H "Authorization: Token SEU_TOKEN" https://api.oneway.mevamfranca.com.br/api/pedidos/
```

## Arquitetura e Componentes

### Estrutura de Arquivos
```
ONEWAY/
├── web/                     # Frontend + Backend Node.js
│   ├── index.html          # SPA com carrinho (1400+ linhas)
│   ├── Css/style.css       # Sistema design + carrinho (2400+ linhas)
│   ├── server.js           # Backend Express + API carrinho (1400+ linhas)
│   ├── products.json       # Base dados produtos
│   ├── mp-success.html     # Página retorno Mercado Pago
│   ├── paypal-success.html # Página retorno PayPal
│   └── img/                # Assets organizados (JPEG)
└── api/                    # Django Admin System
    ├── oneway_admin/       # Configurações Django
    ├── pedidos/            # App principal (models, admin, serializers)
    │   ├── models.py       # Pedido + ItemPedido
    │   ├── admin.py        # Interface com inline para itens
    │   └── migrations/     # Inclui migração de dados
    ├── manage.py           # Django CLI
    └── requirements.txt    # Dependências Python
```

### Sistema de Pagamentos Dinâmico

O sistema suporta múltiplos provedores através de configuração dinâmica:

**Variáveis de Ambiente (Railway):**
```bash
FORMA_PAGAMENTO_CARTAO=MERCADOPAGO  # ou PAYPAL
FORMA_PAGAMENTO_PIX=MERCADOPAGO     # sempre MP (PIX exclusivo)
```

**Fluxo de Pagamento:**
1. Cliente adiciona produtos ao carrinho
2. Carrinho persiste com localStorage
3. Ícone flutuante mostra contador de itens
4. Painel lateral para gerenciar quantidades
5. Seleção de método de pagamento no carrinho
6. Modal coleta dados (nome, email, telefone)
7. Sistema roteia para provedor baseado na configuração
8. PIX → Mercado Pago (5% desconto)
9. Cartão → Mercado Pago ou PayPal (dinâmico)
10. Página de retorno cria pedido no Django
11. Admin permite gestão completa de múltiplos itens

### Models Django Principais

**Comprador:**
- nome, email, telefone, data_cadastro

**Pedido:**
- Relacionamento 1:N com Comprador
- produto (4 camisetas), tamanho (P,M,G,GG), preco (legado)
- forma_pagamento (pix, 2x, 4x, paypal, etc.)
- external_reference (único), payment_id, preference_id
- status_pagamento (pending, approved, rejected, etc.)
- Logs completos com timestamps
- Método total_pedido calcula valor baseado nos itens

**ItemPedido:** ⭐ **NOVO**
- Relacionamento ManyToOne com Pedido
- produto, tamanho, quantidade, preco_unitario
- Propriedade subtotal calculada automaticamente
- Unique constraint por (pedido, produto, tamanho)
- Migração automática de pedidos existentes

### Sistema de Carrinho de Compras ⭐ **NOVO**

Sistema completo implementado com:

**Frontend (JavaScript):**
- Classe `ShoppingCart` com gerenciamento de estado
- Ícone flutuante com contador de itens
- Painel lateral responsivo e minimalista
- Persistência com localStorage
- Controles de quantidade (+/-)
- Seleção de método de pagamento
- Aplicação automática de desconto PIX
- Notificações de item adicionado

**Backend (Node.js):**
- Endpoint `/api/cart/checkout` para múltiplos itens
- Validação de preços contra products.json (segurança)
- Verificação de disponibilidade por tamanho
- Cálculo automático de totais
- Aplicação de desconto PIX nos preços unitários

**Django Admin:**
- Modelo `ItemPedido` com inline
- Exibição de resumo dos itens
- Cálculo automático de totais
- Migração de pedidos legados preservada

**Estrutura do Carrinho:**
```javascript
cart = {
  items: [
    {
      productId: 'camiseta-marrom',
      title: 'Camiseta One Way Marrom',
      size: 'M',
      quantity: 2,
      price: 120.00,
      image: './img/...'
    }
  ]
}
```

### Sistema products.json

Base de dados de produtos com estrutura:
```json
{
  "products": {
    "camiseta-marrom": {
      "id": "1",
      "title": "Camiseta One Way Marrom", 
      "price": 120.00,
      "preco_custo": 53.50,
      "image": "./img/camisetas/camiseta_marrom.jpeg",
      "sizes": {
        "P": {
          "available": true,
          "qtda_estoque": 8,
          "stripe_link": "...",
          "id_stripe": "..."
        }
      }
    }
  }
}
```

## Configurações de Produção

### Variáveis de Ambiente

**Node.js (WEB Service):**
```bash
MERCADOPAGO_ACCESS_TOKEN=APP_USR_xxx
DJANGO_API_URL=https://api.oneway.mevamfranca.com.br/api
DJANGO_API_TOKEN=xxx
MP_SUCCESS_URL=https://oneway.mevamfranca.com.br/mp-success
MP_CANCEL_URL=https://oneway.mevamfranca.com.br/mp-cancel
FORMA_PAGAMENTO_CARTAO=MERCADOPAGO  # ou PAYPAL
FORMA_PAGAMENTO_PIX=MERCADOPAGO

# PayPal (quando ativo)
PAYPAL_CLIENT_ID=xxx
PAYPAL_CLIENT_SECRET=xxx
PAYPAL_ENVIRONMENT=production
```

**Django (API Service):**
```bash
DATABASE_URL=postgresql://xxx  # Auto-configurado Railway
DJANGO_SECRET_KEY=xxx
DEBUG=False
MERCADOPAGO_ACCESS_TOKEN=APP_USR_xxx
```

### Sistema de Segurança

- ✅ **Preços protegidos**: Sempre vindos do products.json (servidor)
- ✅ **Token API**: Autenticação Django ↔ Node.js
- ✅ **CORS/CSRF**: Configurados para domínios autorizados
- ✅ **Validação tripla**: Frontend + Backend + Django
- ✅ **Logs anti-fraude**: Detecção tentativas manipulação

## Desenvolvimento e Issues

### Status Implementação
- ✅ **Issues #11-14, #17-19, #22-28**: Fluxo Mercado Pago completo
- ✅ **Issues #39-44**: Integração PayPal com configuração dinâmica
- ✅ **Issues #46-53**: Sistema carrinho de compras completo ⭐ **NOVO**
- 🔄 **Issues #32-38**: Sistema controle estoque (planejado)
- ⏳ **Issue #45**: Pagamento presencial na igreja (planejado)

### Metodologia Issues
- **code-complete**: Código implementado, mas não testado
- **testing**: Em fase de testes
- **validated**: Testado e funcionando
- **closed**: Entregue e validado

### Problemas Conhecidos
- ❌ **Botão "Consultar Status MP"**: Implementado mas não funcional
- ⚠️ **PayPal guest checkout**: Pode forçar criação conta (limitação API)

## Tecnologias e Dependências

**Frontend:** HTML5, CSS3, JavaScript ES6+ (vanilla)  
**Backend:** Node.js 18+, Express.js  
**Admin:** Django 5.2.4, Django REST Framework 3.16.0  
**Banco:** PostgreSQL (Railway), SQLite (local)  
**Pagamentos:** Mercado Pago API, PayPal REST API  
**Deploy:** Railway (auto-deploy, custom domains)  

**Estatísticas:**
- ~7500 linhas código total (HTML/CSS/JS + Python)
- 53+ issues criadas (8 fechadas hoje ✅)
- Sistema carrinho + dual pagamentos operacional
- PostgreSQL persistente com zero downtime
- Migração automática de dados sem perda
- 100% funcionalidades do carrinho implementadas ⭐

---

## Lembrete Final

**O sistema está em PRODUÇÃO ATIVA** servindo clientes reais. Sempre teste mudanças localmente e use logs detalhados para debugging. Railway faz deploy automático - cuidado com commits diretos na main.