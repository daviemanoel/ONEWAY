# Django Admin - Sistema de Gestão ONE WAY

Documentação completa do sistema administrativo Django para gestão de pedidos do evento ONE WAY 2025.

## 🚀 Acesso Rápido

- **URL Produção**: [https://api.oneway.mevamfranca.com.br/admin/](https://api.oneway.mevamfranca.com.br/admin/)
- **Credenciais**: admin / oneway2025
- **API REST**: [https://api.oneway.mevamfranca.com.br/api/](https://api.oneway.mevamfranca.com.br/api/)

## 📋 Funcionalidades Principais

### ✅ Gestão de Pedidos
- **Visualização completa** de todos os pedidos
- **Filtros avançados** por status, produto, forma de pagamento
- **Busca** por nome, email, payment_id
- **Ações em lote** para múltiplos pedidos
- **Links diretos** para Mercado Pago

### ✅ Gestão de Compradores
- **Cadastro automático** via site
- **Histórico de pedidos** por comprador
- **Dados de contato** organizados
- **Relacionamento 1:N** com pedidos

### ✅ Relatórios e Métricas
- **Dashboard** com estatísticas
- **Vendas por produto** e tamanho
- **Formas de pagamento** mais utilizadas
- **Status dos pedidos** em tempo real
- **Receita total** e por período

## 🏗️ Arquitetura do Sistema

### Models Principais

#### Comprador
```python
class Comprador(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    data_cadastro = models.DateTimeField(auto_now_add=True)
```

#### Pedido
```python
class Pedido(models.Model):
    comprador = models.ForeignKey(Comprador, on_delete=models.CASCADE)
    produto = models.CharField(max_length=100)
    tamanho = models.CharField(max_length=5)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    forma_pagamento = models.CharField(max_length=20)
    
    # Dados Mercado Pago
    external_reference = models.CharField(max_length=100, unique=True)
    payment_id = models.CharField(max_length=50)
    preference_id = models.CharField(max_length=100)
    merchant_order_id = models.CharField(max_length=50)
    
    # Status e Controle
    status_pagamento = models.CharField(max_length=20, default='pending')
    data_pedido = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(blank=True)
```

## 🔧 Configuração e Setup

### Desenvolvimento Local

```bash
cd api
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Produção Railway

```bash
# Setup automático
python manage.py setup_database

# Criar token API para Node.js
python manage.py criar_token_api --username api_nodejs
```

### Variáveis de Ambiente

```bash
DATABASE_URL=postgresql://xxx  # Auto-configurado Railway
DJANGO_SECRET_KEY=xxx
DEBUG=False
MERCADOPAGO_ACCESS_TOKEN=APP_USR_xxx
```

## 🌐 API REST Endpoints

### Autenticação
```bash
# Header necessário
Authorization: Token SEU_TOKEN_AQUI
```

### Endpoints Disponíveis

#### Pedidos
```bash
# Listar todos os pedidos
GET /api/pedidos/

# Criar novo pedido
POST /api/pedidos/
{
    "comprador": {
        "nome": "João Silva",
        "email": "joao@email.com",
        "telefone": "(16) 99999-9999"
    },
    "produto": "Camiseta One Way Marrom",
    "tamanho": "M",
    "preco": 120.00,
    "forma_pagamento": "pix",
    "external_reference": "Camiseta_M_1641234567"
}

# Buscar pedido específico
GET /api/pedidos/{external_reference}/

# Atualizar status do pedido
PUT /api/pedidos/{external_reference}/
{
    "payment_id": "1234567890",
    "status_pagamento": "approved"
}
```

#### Detalhes Mercado Pago
```bash
# Consultar detalhes do pagamento
GET /api/mp-payment-details/{payment_id}/
```

### Exemplo de Uso
```bash
# Testar API
curl -H "Authorization: Token SEU_TOKEN" \
     https://api.oneway.mevamfranca.com.br/api/pedidos/

# Criar pedido
curl -X POST \
     -H "Authorization: Token SEU_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"comprador": {...}, "produto": "..."}' \
     https://api.oneway.mevamfranca.com.br/api/pedidos/
```

## 🎛️ Interface Admin

### Dashboard Principal
- **Estatísticas gerais** (total de pedidos, receita, etc.)
- **Gráficos** de vendas por período
- **Alertas** de pedidos pendentes
- **Links rápidos** para principais seções

### Gestão de Pedidos
- **Lista paginada** com filtros
- **Cores por status**: Verde (approved), Amarelo (pending), Vermelho (rejected)
- **Ações disponíveis**:
  - Ver detalhes completos
  - Consultar status no MP
  - Atualizar status manualmente
  - Adicionar observações
  - Exportar relatórios

### Filtros Disponíveis
- **Status do pagamento**: Approved, Pending, Rejected
- **Produto**: Por tipo de camiseta
- **Tamanho**: P, M, G, GG
- **Forma de pagamento**: PIX, 2x, 4x
- **Data**: Por período específico

### Buscas
- **Nome do comprador**
- **Email**
- **Payment ID**
- **External Reference**
- **Telefone**

## 🔍 Funcionalidades Avançadas

### Consulta Status Mercado Pago
- **Botão integrado** na interface admin
- **Atualização automática** do status
- **Logs de auditoria** das consultas
- **Tratamento de erros** da API MP

### Relatórios Personalizados
- **Vendas por produto**
- **Receita por período**
- **Formas de pagamento mais usadas**
- **Taxa de conversão** por canal
- **Export em CSV/Excel**

### Ações em Lote
- **Atualizar status** de múltiplos pedidos
- **Exportar** dados selecionados
- **Marcar como processado**
- **Adicionar observações** em massa

## 🛠️ Comandos Úteis

### Django Management Commands
```bash
# Setup completo do banco
python manage.py setup_database

# Criar token API
python manage.py criar_token_api --username api_nodejs

# Migrar banco
python manage.py migrate

# Criar superuser
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic
```

### Diagnóstico e Manutenção
```bash
# Testar conexão com banco
python test_db.py

# Recuperar banco em caso de problemas
python fix_db.py

# Logs Railway
railway logs --service API -f
```

## 🔒 Segurança

### Configurações Implementadas
- **CORS** configurado para domínios específicos
- **CSRF** protection ativo
- **Token authentication** para API
- **Staff-only access** para admin
- **SQL injection** protegido por Django ORM

### Domínios Autorizados
```python
CORS_ALLOWED_ORIGINS = [
    "https://oneway.mevamfranca.com.br",
    "https://api.oneway.mevamfranca.com.br",
    "http://localhost:3000",  # Desenvolvimento
]
```

## 📊 Monitoramento

### Logs Disponíveis
- **Acesso ao admin** (Django logs)
- **Requisições API** (DRF logs)
- **Consultas MP** (Custom logs)
- **Erros de sistema** (Railway logs)

### Métricas Importantes
- **Tempo de resposta** da API
- **Taxa de sucesso** dos pagamentos
- **Uso de recursos** Railway
- **Erros 4xx/5xx**

## 🚀 Deploy e Produção

### Railway Configuration
- **Auto-deploy** do branch main
- **PostgreSQL** gerenciado
- **SSL** automático
- **Backup** automático do banco

### Health Checks
```bash
# Status da API
curl https://api.oneway.mevamfranca.com.br/api/

# Admin disponível
curl https://api.oneway.mevamfranca.com.br/admin/
```

### Monitoramento
- **Railway dashboard** para métricas
- **Django admin logs** para auditoria
- **PostgreSQL stats** via Railway

## 📞 Suporte e Troubleshooting

### Problemas Comuns
1. **Token inválido**: Gerar novo token via admin
2. **CORS error**: Verificar domínio em settings.py
3. **Banco desconectado**: Executar fix_db.py
4. **API lenta**: Verificar logs Railway

### Contatos
- **Admin URL**: https://api.oneway.mevamfranca.com.br/admin/
- **Logs Railway**: `railway logs --service API`
- **Documentação**: Ver README.md principal

---

**Sistema em produção** | Última atualização: Julho 2025