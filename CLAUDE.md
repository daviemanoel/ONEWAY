# CLAUDE.md

Este arquivo fornece orientações para o Claude Code (claude.ai/code) ao trabalhar com código neste repositório.

## PRINCÍPIOS IMPORTANTES
- **SEMPRE responder em português brasileiro**
- **SEMPRE perguntar antes de gerar código** (regra obrigatória)
- Usar terminologia técnica em português quando possível
- Manter consistência com o idioma do projeto (site em português)
- Preferir soluções simples e diretas em vez de múltiplas opções

## Visão Geral do Projeto
Este é um site estático para o evento de conferência jovem "ONE WAY" (31 de julho - 2 de agosto de 2025). É uma aplicação de página única construída com HTML, CSS e JavaScript vanilla, com backend Node.js/Express para processamento de pagamentos.

### Arquitetura do Sistema
```
[Frontend HTML/JS] → [Node.js/Express] → [Mercado Pago API]
        ↓                    ↓
[products.json]    [Django REST API] → [PostgreSQL Railway]
        ↓                    ↓
[Cache 5min]       [Admin Interface] → [Gestão Completa]
```

### Status do Projeto: 🚀 **PRODUÇÃO ATIVA**
- ✅ **Frontend**: Deploy contínuo via Railway
- ✅ **Backend**: Node.js + Express funcional
- ✅ **Pagamentos**: Mercado Pago integrado com métodos dinâmicos
- ✅ **Admin**: Django com PostgreSQL persistente
- ✅ **E-commerce**: Fluxo completo de pedidos implementado

## Comandos de Desenvolvimento

### Railway CLI (Produção)
- **Logs em tempo real**: `railway logs -f`
- **Status**: `railway status`
- **Deploy forçado**: `railway up`
- **Executar comando**: `railway run --service API <comando>`
- **Conectar projeto**: `railway link` (escolher ONEWAY → API)

### Frontend (Site estático)
- **Rodar localmente**: Abra `index.html` diretamente no navegador ou use um servidor local como `python -m http.server 8000` ou `npx serve`
- **Sem comandos de build/lint/teste** - É puro HTML/CSS/JS sem ferramentas

### Backend (Processamento de pagamentos)
- **Servidor local**: `cd web && node server.js` na porta 3000
- **Scripts disponíveis**: `npm start` ou `npm run dev`
- **Deploy**: Railway (https://oneway.mevamfranca.com.br)
- **Dependências**: `cd web && npm install` (express, cors, stripe, mercadopago, dotenv)
- **Node.js**: >= 18.0.0 (especificado em package.json)
- **Variáveis ambiente**: STRIPE_SECRET_KEY, MERCADOPAGO_ACCESS_TOKEN

### Django Admin (Sistema de gestão)
- **Ambiente local**: `cd api && python manage.py runserver` (SQLite local)
- **Produção Railway**: PostgreSQL gerenciado com dados persistentes
- **Migrar localmente**: `python manage.py migrate`
- **Setup completo produção**: `python manage.py setup_database` (comando personalizado)
- **Admin produção**: https://api.oneway.mevamfranca.com.br/admin/ (admin/oneway2025)
- **API Token**: Criar no Django Admin em `/admin/authtoken/tokenproxy/` (integração Node.js)
- **Comandos customizados**: `python manage.py criar_token_api --username api_nodejs`
- **Consulta MP**: ⚠️ **EM DESENVOLVIMENTO** - Botão implementado mas com problemas de conectividade
- **Dependências**: Django 5.2.4, DRF 3.16.0, psycopg2-binary 2.9.9
- **Models**: Comprador, Pedido com relacionamento 1:N
- **API REST**: Endpoints para CRUD completo de pedidos

### Comandos Úteis de Gestão
- **Testar API**: `curl -H "Authorization: Token SEU_TOKEN" https://api.oneway.mevamfranca.com.br/api/pedidos/`
- **Reset DB local**: `rm db.sqlite3 && python manage.py migrate && python manage.py createsuperuser`
- **Logs produção**: `railway logs --service API`
- **Deploy forçado**: `railway up --service API`
- **Diagnóstico DB**: `python test_db.py` (script de 125 linhas)
- **Recuperação DB**: `python fix_db.py` (em caso de problemas)
- **Health checks**: `/health` (Node.js), `/mp-health` (Mercado Pago), `/admin/` (Django)

### Comandos do Sistema de Estoque (Planejados - Issues #32-38)
- **Migrar produtos**: `python manage.py migrar_produtos` (Issue #34)
- **Sincronizar estoque**: `python manage.py sincronizar_estoque` (Issue #36)
- **Associar pedidos legacy**: `python manage.py associar_pedidos_legacy` (Issue #34)
- **Gerar products.json**: `python manage.py gerar_products_json` (Issue #36)
- **Validar estoque**: `python manage.py validar_estoque` (Issue #38)
- **Relatório estoque**: `python manage.py relatorio_estoque` (Issue #38)
- **Cron automático**: `*/5 * * * * python manage.py sincronizar_estoque` (Issue #38)

## Arquitetura e Componentes Principais

### Estrutura de Arquivos
```
ONEWAY/
├── web/                          # Frontend estático
│   ├── index.html               # SPA principal (500+ linhas)
│   ├── Css/style.css           # Estilos completos (1655+ linhas)
│   ├── server.js               # Backend Node.js/Express
│   ├── products.json           # Base de dados produtos
│   ├── mp-success.html         # Captura dados Mercado Pago
│   └── img/                    # Assets organizados
└── api/                         # Django Admin System
    ├── oneway_admin/           # Configurações Django
    ├── pedidos/                # App principal com models
    ├── manage.py               # Django CLI
    ├── requirements.txt        # Dependências Python
    └── Dockerfile              # Deploy Railway
```

### Ordem Atual das Seções (após reordenação)
```
index.html (SPA estática)
├── Header: Navegação fixa com glassmorphism
├── #home: Hero banner principal
├── #sobre: Conteúdo institucional do evento
├── #produtos: Camisetas carregadas via products.json
├── #minha-secao: Ingressos em layout tabela (Date + Tickets combinados)
├── #faq: FAQ interativo com accordion
└── Rodapé: Logo simples
```

### Sistema de Produtos Dinâmicos
- **products.json** contém 4 camisetas com configuração completa por tamanho
- Carregamento via JavaScript assíncrono com função `loadProducts()`
- Integração com backend para processamento via Mercado Pago
- Seleção de tamanhos com botões interativos (P, M, G, GG)
- Seletor de forma de pagamento (PIX 5% OFF, 2x sem juros, até 4x)
- Grid responsivo: 4 colunas desktop → 1 coluna mobile (vertical)
- Preços, custos e estoque controlados via JSON
- Galeria de imagens/vídeos com navegação por dots

### Sistema de Navegação e Layout
- **Header fixo** com efeito blur e transparência ao rolar
- **Smooth scroll** entre seções com âncoras
- **Menu hamburger** responsivo para mobile com auto-close
- **Layout tabela** para seção ingressos (Date + Tickets combinados)
- **Breakpoint principal**: 768px para mobile/desktop

### Integração de Pagamentos Completa
- **Ingressos**: tiketo.com.br (links diretos, 3 lotes ativos)
- **Produtos**: Sistema completo Mercado Pago + Django
- **Fluxo Seguro**: Frontend → MP → Registro automático no banco
- **Validação**: Formulário obrigatório + seleção produto/pagamento

### Sistema de Pagamento Otimizado (Mercado Pago)
- **PIX**: 5% de desconto automático
- **Cartão**: Até 2x sem juros, até 4x com juros
- **Métodos Dinâmicos**: Configuração baseada na escolha do usuário (Issue #24)
- **Segurança**: Preços sempre do servidor (products.json)
- **Anti-fraude**: Logs de tentativas de manipulação
- **Checkout**: Sem login obrigatório + UX otimizada
- **Gestão**: Admin Django com controle total
- **Status**: Sincronização automática com MP
- **Dados limpos**: Zero registros "fantasma"

### Estrutura products.json
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

### Status Implementação
- ✅ Backend Node.js/Express configurado
- ✅ Integração Mercado Pago completa
- ✅ Frontend com seletor de pagamento
- ✅ PIX com desconto de 5%
- ✅ Parcelamento até 4x
- ✅ Páginas de retorno configuradas
- ✅ Deploy no Railway funcionando
- ✅ Imagens convertidas para JPEG (compatibilidade)
- ✅ **Issue #11**: Captura dados MP implementada (mp-success.html)
- ✅ **Issue #12**: Django Admin completo com PostgreSQL
- ✅ **Issue #13**: API REST Django-Node.js funcional
- ✅ **Issue #14**: Formulário de dados do comprador (implementado)
- ✅ **Issue #17**: Fluxo otimizado - sem registros imediatos
- ✅ **Issue #18**: Criação retroativa na página de sucesso
- ✅ **Issue #24**: Métodos de pagamento dinâmicos implementados
- ✅ **Railway Deploy**: PostgreSQL persistente, dados preservados entre deploys
- ✅ **Comando personalizado**: setup_database para inicialização automática
- ✅ **Segurança**: Preços sempre vindos do servidor (products.json)
- ✅ **Admin funcional**: Links MP, consulta status, gestão completa
- ✅ **Cancelamento automático**: Processamento de pedidos cancelados
- ✅ **Preços atualizados**: Todas as camisetas com R$ 120,00

## FLUXO COMPLETO DE PAGAMENTO OTIMIZADO

### Sistema Atual Implementado ✅
**Objetivo ALCANÇADO**: Sistema completo de e-commerce com gestão de pedidos sem registros "fantasma".

#### Fluxo de Pagamento Seguro:
```
1. Cliente navega pelo site e escolhe produto + tamanho
2. Clica no botão "Comprar" do produto desejado
3. Modal abre → Preenche formulário obrigatório (nome, email, telefone)
4. Escolhe forma de pagamento (PIX -5%, 2x ou 4x)
5. Clica "Pagar" → Cria preferência MP (SEM registro no banco)
6. Redireciona para checkout do Mercado Pago
7. No Mercado Pago:
   - Se paga → Redireciona para mp-success.html
   - Se cancela → Redireciona para mp-cancel.html
8. Em mp-success.html:
   - Detecta status=approved → Cria registros no Django
   - Exibe confirmação visual + ID do pedido
9. Em mp-cancel.html:
   - Exibe mensagem de cancelamento
   - Oferece botão para voltar ao site
```

#### Issues Implementadas e Funcionais:
1. **[#11 - Capturar dados MP](https://github.com/daviemanoel/ONEWAY/issues/11)** ✅ **COMPLETO**
   - JavaScript avançado em `mp-success.html` 
   - Captura parâmetros MP + dados comprador via URL
   - Estados visuais: loading, sucesso, erro, já processado

2. **[#12 - Admin Django](https://github.com/daviemanoel/ONEWAY/issues/12)** ✅ **COMPLETO**
   - Models: Comprador e Pedido com relacionamento
   - Admin customizado: filtros, buscas, actions, status coloridos
   - Links funcionais para Mercado Pago
   - ⚠️ Botão "Consultar Status MP" implementado mas com problemas de conectividade
   - PostgreSQL Railway com dados persistentes

3. **[#13 - API REST Django-Node.js](https://github.com/daviemanoel/ONEWAY/issues/13)** ✅ **COMPLETO**
   - Django REST Framework com token authentication
   - Endpoints: `/api/pedidos/`, `/api/mp-payment-details/`
   - Proxy Node.js para comunicação segura
   - Serializers com validação e criação atômica

4. **[#14 - Formulário comprador](https://github.com/daviemanoel/ONEWAY/issues/14)** ✅ **COMPLETO**
   - Modal responsivo com validação JavaScript
   - Campos: nome, email, telefone (todos obrigatórios)
   - Máscara de telefone brasileiro
   - Integração com fluxo de pagamento

5. **[#17 - Fluxo otimizado](https://github.com/daviemanoel/ONEWAY/issues/17)** ✅ **COMPLETO**
   - Removida criação imediata de registros
   - Dados do comprador incluídos na URL de retorno
   - Cache de produtos.json para performance
   - Logs de segurança anti-fraude

6. **[#18 - Criação retroativa](https://github.com/daviemanoel/ONEWAY/issues/18)** ✅ **COMPLETO**
   - Registros criados apenas quando pagamento aprovado
   - Fallback para metadata MP se necessário
   - Detecção de duplicatas
   - Feedback visual completo

7. **[#24 - Métodos de pagamento dinâmicos](https://github.com/daviemanoel/ONEWAY/issues/24)** ✅ **COMPLETO**
   - Configuração dinâmica baseada na escolha do usuário
   - **PIX**: Exclui cartões de crédito e débito (apenas PIX + conta MP)
   - **2x sem juros**: Exclui PIX, limita a 2 parcelas
   - **4x com juros**: Exclui PIX, permite até 4 parcelas
   - Resolve inconsistência entre seleção no site e checkout MP
   - Implementado em `server.js:293-338` com logs de debug

8. **[#25 - Testes de validação](https://github.com/daviemanoel/ONEWAY/issues/25)** ✅ **COMPLETO**
   - Testes realizados em produção com sucesso
   - Comportamento validado para todos os métodos de pagamento

9. **[#27-28 - Melhorias finais](https://github.com/daviemanoel/ONEWAY/issues/27)** ✅ **COMPLETO**
   - Processamento automático de cancelamentos
   - Refatoração de external_reference

### 🚀 **IMPLEMENTAÇÃO PAYPAL COMPLETA** ✅

**Issues Implementadas**: **[#39-#44 - Integração PayPal](https://github.com/daviemanoel/ONEWAY/issues/39)**

#### **✅ Sistema PayPal Funcional (Commit 0c97cac)**
- ✅ **[#39 - PayPal como método alternativo](https://github.com/daviemanoel/ONEWAY/issues/39)** ✅ **COMPLETO**
  - PayPal como opção adicional ao Mercado Pago
  - Sistema de configuração dinâmica via variáveis de ambiente
  - Melhoria na taxa de aprovação para cartões de crédito

- ✅ **[#40 - Endpoints Node.js](https://github.com/daviemanoel/ONEWAY/issues/40)** ✅ **COMPLETO**
  - `/create-paypal-order` - Criação de pedidos PayPal
  - `/capture-paypal-order` - Captura de pagamentos
  - `/api/payment-config` - Configuração dinâmica
  - Integração completa com Django API

- ✅ **[#41 - Frontend PayPal](https://github.com/daviemanoel/ONEWAY/issues/41)** ✅ **COMPLETO**
  - Sistema de roteamento dinâmico baseado em configuração
  - Páginas `paypal-success.html` e `paypal-cancel.html`
  - UX integrada com design existente

- ✅ **[#42 - Django Models](https://github.com/daviemanoel/ONEWAY/issues/42)** ✅ **COMPLETO**
  - 'paypal' em `FORMA_PAGAMENTO_CHOICES`
  - Migration `0002_alter_pedido_forma_pagamento`
  - Admin interface com links PayPal funcionais

- ⏳ **[#43 - Deploy Railway](https://github.com/daviemanoel/ONEWAY/issues/43)** ⏳ **AGUARDANDO CREDENCIAIS**
  - Código 100% pronto para produção
  - Aguardando configuração de credenciais PayPal
  - Documentação completa incluída

- ✅ **[#44 - Testes PayPal](https://github.com/daviemanoel/ONEWAY/issues/44)** ✅ **COMPLETO**
  - Scripts de teste de credenciais e funcionalidade
  - Logs detalhados para debug
  - Validação automática de integração

#### **🔧 Configuração Dinâmica Implementada:**
```bash
# Variáveis de Ambiente (Railway)
FORMA_PAGAMENTO_CARTAO=MERCADOPAGO  # ou PAYPAL
FORMA_PAGAMENTO_PIX=MERCADOPAGO     # fixo
PAYPAL_CLIENT_ID=seu_client_id      # quando ativar PayPal
PAYPAL_CLIENT_SECRET=seu_secret     # quando ativar PayPal
PAYPAL_ENVIRONMENT=production       # ou sandbox
```

#### **🎯 Funcionalidades PayPal:**
1. **Cartões de crédito** via PayPal (melhor aprovação)
2. **PIX mantido** no Mercado Pago (5% desconto)
3. **Configuração dinâmica** sem alteração de código
4. **Interface unificada** para o usuário
5. **Admin Django** com suporte completo PayPal
6. **Páginas de retorno** customizadas

#### **📊 Status PayPal:**
- 🚀 **Código**: 100% implementado e testado
- 📚 **Documentação**: `paypal-integration-guide.md` completo
- 🔧 **Deploy**: Pronto, aguardando credenciais
- 💰 **Benefícios**: Maior taxa de aprovação, público internacional
- 🔄 **Compatibilidade**: Zero impacto no sistema atual

---

#### Próximas Implementações:

### 🚀 **PRIORIDADE ALTA: Sistema de Controle de Estoque**

**Issue Principal**: **[#32 - Sistema de controle de estoque com models Django](https://github.com/daviemanoel/ONEWAY/issues/32)**

**Roadmap de Implementação:**

#### **📋 Fase 1: Foundation (Issue #33)**
- **[#33 - Models Produto e ProdutoTamanho](https://github.com/daviemanoel/ONEWAY/issues/33)** 🔄 **PLANEJADO**
  - Criar models Django para produtos e tamanhos
  - Migration segura com campos nullable
  - Manter compatibilidade com sistema atual

#### **📋 Fase 2: Data Migration (Issues #34-35)**
- **[#34 - Migração de dados products.json → Django](https://github.com/daviemanoel/ONEWAY/issues/34)** 🔄 **PLANEJADO**
  - Script para popular models com dados existentes
  - Comando Django para migração idempotente
  - Associação de pedidos legacy aos novos models

- **[#35 - Interface admin Django](https://github.com/daviemanoel/ONEWAY/issues/35)** 🔄 **PLANEJADO**
  - Admin interface para gerenciar produtos e estoque
  - Edição inline de tamanhos e quantidades
  - Ações em lote para sincronização

#### **📋 Fase 3: Integration (Issues #36-37)**
- **[#36 - Comando sincronização híbrido](https://github.com/daviemanoel/ONEWAY/issues/36)** 🔄 **PLANEJADO**
  - Comando Django para sincronizar estoque automaticamente
  - Suporte a pedidos novos e legacy
  - Geração automática do products.json

- **[#37 - Frontend com IDs numéricos](https://github.com/daviemanoel/ONEWAY/issues/37)** 🔄 **PLANEJADO**
  - Modificar frontend para usar IDs numéricos do Django
  - Validação de estoque em tempo real
  - Manter compatibilidade com sistema atual

#### **📋 Fase 4: Production (Issue #38)**
- **[#38 - Deploy Railway com automação](https://github.com/daviemanoel/ONEWAY/issues/38)** 🔄 **PLANEJADO**
  - Cron jobs para sincronização automática
  - Monitoramento e alertas de estoque
  - Backup e rollback plan

#### **🎯 Objetivos do Sistema de Estoque:**
1. **Controle automático** de estoque baseado em pedidos aprovados
2. **Sincronização** entre Django e products.json
3. **Compatibilidade total** com sistema atual (zero downtime)
4. **IDs numéricos** para produto+tamanho
5. **Validação** em tempo real no checkout
6. **Automação** via cron jobs e webhooks

#### **🔧 Estrutura Técnica Proposta:**
```python
# Models Django
class Produto(models.Model):
    nome = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2)
    ativo = models.BooleanField(default=True)
    json_key = models.CharField(max_length=100)  # Compatibilidade

class ProdutoTamanho(models.Model):
    produto = models.ForeignKey(Produto, related_name='tamanhos')
    tamanho = models.CharField(max_length=5, choices=TAMANHOS_CHOICES)
    estoque = models.IntegerField(default=0)
    disponivel = models.BooleanField(default=True)

class Pedido(models.Model):
    # ... campos existentes ...
    produto_tamanho = models.ForeignKey(ProdutoTamanho, null=True, blank=True)
    estoque_decrementado = models.BooleanField(default=False)
```

#### **🚀 Outras Implementações:**
- ⚠️ **URGENTE: Fix botão Consultar MP** - Resolver conectividade com API MP
- **[Issue #15](https://github.com/daviemanoel/ONEWAY/issues/15)**: Webhook MP para automação total (não crítico)
- **[Issue #26](https://github.com/daviemanoel/ONEWAY/issues/26)**: Atualização da documentação ✅ **EM ANDAMENTO**
- **Relatórios**: Dashboard de vendas e métricas
- **Notificações**: Email automático para compradores
- **Otimizações**: Melhorias de performance e UX

#### Problemas Conhecidos:
- ❌ **Botão "Consultar Status MP"**: Implementado com JavaScript, CSS e endpoint Django, mas não está funcionando em produção
  - Código completo em: `api/pedidos/static/admin/js/consultar_mp.js`
  - Endpoint: `/consultar-mp/` com autenticação staff_member_required
  - Token MP configurado no Railway
  - Precisa investigar logs detalhados e debugging
- ✅ **Logs de debug**: Funcionando em `server.js` para monitorar configuração de métodos de pagamento

#### Detalhes Técnicos - Métodos de Pagamento Dinâmicos:

**Configuração no server.js (linhas 293-338):**
```javascript
// PIX selecionado:
payment_methods.excluded_payment_types = [
  { id: 'ticket' },      // Boletos
  { id: 'credit_card' }, // Cartão crédito
  { id: 'debit_card' }   // Cartão débito
];

// 2x ou 4x selecionado:
payment_methods.excluded_payment_types = [
  { id: 'ticket' },        // Boletos
  { id: 'bank_transfer' }  // PIX
];
```

**Logs implementados:**
- `🔧 Configurando métodos de pagamento para: [método]`
- `✅ PIX: Cartões excluídos`
- `✅ 2x: PIX excluído, máximo 2 parcelas`
- `✅ 4x: PIX excluído, máximo 4 parcelas`

#### Arquitetura Final Implementada:
```
[Frontend HTML/JS] → [Node.js/Express] → [Mercado Pago API]
        ↓                    ↓                    ↓
[products.json]    [Proxy Endpoints]    [Métodos Dinâmicos]
        ↓                    ↓                    ↓
[Cache 5min]       [Django REST API] → [PostgreSQL Railway]
                            ↓
                    [Admin Interface] → [Gestão Completa]
```

#### Arquitetura Futura com Sistema de Estoque (Issues #32-38):
```
[Frontend HTML/JS] → [Node.js/Express] → [Mercado Pago API]
        ↓                    ↓                    ↓
[products.json] ← [Sync Auto]    [Proxy Endpoints]    [Métodos Dinâmicos]
        ↓                    ↓                    ↓
[Cache 5min]       [Django REST API] → [PostgreSQL Railway]
                            ↓                    ↓
                    [Admin Interface] → [Produto + ProdutoTamanho Models]
                            ↓                    ↓
                    [Cron Jobs] → [Controle Automático de Estoque]
```

**Melhorias Planejadas:**
- 🔄 **Sincronização Automática**: products.json gerado pelo Django
- 📊 **Controle Real-time**: Estoque atualizado com pedidos aprovados
- 🆔 **IDs Numéricos**: Produto+tamanho com identificadores únicos
- 🔁 **Sistema Híbrido**: Suporte a pedidos legacy e novos
- ⚡ **Performance**: Validação de estoque em tempo real
- 🤖 **Automação**: Cron jobs para sincronização contínua

#### Fluxo de Pagamento Completo:
1. **Cliente** preenche formulário (nome, email, telefone)
2. **Seleciona** produto + tamanho + forma de pagamento
3. **Node.js** cria pedido pendente no Django
4. **Mercado Pago** recebe preferência com métodos dinâmicos
5. **Cliente** paga no checkout MP
6. **Página sucesso** atualiza status do pedido
7. **Django Admin** permite gestão completa

## Observações Técnicas Importantes

### Deploy e Banco de Dados
- **PostgreSQL Railway**: Banco persistente, dados nunca são perdidos entre deploys
- **Comando setup_database**: Criação automática de tabelas Django + superuser admin/oneway2025
- **WhiteNoise**: Serve arquivos estáticos CSS/JS do Django Admin corretamente
- **Configuração híbrida**: Auto-detecta PostgreSQL produção / SQLite local via DATABASE_URL
- **Scripts diagnóstico**: test_db.py (análise completa), fix_db.py (recuperação)
- **Dockerfile otimizado**: Python 3.11-slim, gunicorn, collectstatic automático
- **Runtime**: Node.js >= 18.0.0, Python 3.11.9

### Frontend e UX
- **JavaScript inline**: Todo código JS está no index.html (744 linhas)
- **CSS modular**: style.css (2048 linhas), modal-checkout.css, pedidos_admin.css
- **Lazy loading**: Imagens otimizadas exceto hero banner
- **Mobile-first**: Breakpoint principal 768px, design responsivo completo
- **Assets**: Todas imagens convertidas para JPEG (compatibilidade Linux)
- **Cache**: Sistema de 5 minutos para products.json
- **Total código**: 3.477 linhas (HTML/CSS/JS core)

## Configurações de Produção

### Variáveis de Ambiente Necessárias
```bash
# Node.js (Railway Web Service)
MERCADOPAGO_ACCESS_TOKEN=APP_USR_xxx  # Token produção MP
DJANGO_API_URL=https://api.oneway.mevamfranca.com.br/api
DJANGO_API_TOKEN=xxx  # Token gerado pelo Django
MP_SUCCESS_URL=https://oneway.mevamfranca.com.br/mp-success
MP_CANCEL_URL=https://oneway.mevamfranca.com.br/mp-cancel

# Django (Railway API Service)  
DATABASE_URL=postgresql://xxx  # Auto-configurado pelo Railway
DJANGO_SECRET_KEY=xxx
DEBUG=False
MERCADOPAGO_ACCESS_TOKEN=APP_USR_xxx  # Para consultas admin
```

### Segurança Implementada
- ✅ **Preços protegidos**: Sempre vindos do products.json servidor
- ✅ **Token API**: Autenticação segura Django ↔ Node.js
- ✅ **CORS configurado**: Apenas domínios autorizados Railway/localhost
- ✅ **CSRF Protection**: Trusted origins configurados
- ✅ **Security Headers**: XSS, HSTS, Content-Type configurados
- ✅ **Logs anti-fraude**: Detecção de tentativas de manipulação
- ✅ **Validação dupla**: Frontend + backend + Django
- ✅ **PostgreSQL**: Banco persistente e seguro

### URLs de Produção
- **Frontend**: https://oneway.mevamfranca.com.br/
- **Django Admin**: https://api.oneway.mevamfranca.com.br/admin/
- **API REST**: https://api.oneway.mevamfranca.com.br/api/
- **Health Check**: https://oneway.mevamfranca.com.br/health
- **MP Health**: https://oneway.mevamfranca.com.br/mp-health

### Limitações Conhecidas (Menores)
- ⚠️ Cliente pode alterar método no checkout MP (preço permanece correto)
- ⚠️ Links MP admin podem precisar ajuste conforme painel MP
- ⚠️ Checkout sem login MP (trade-off: UX vs conversão)
- ⚠️ Stripe mantido no código (legacy, não usado)
- ✅ **Issue #24 resolvida**: Métodos de pagamento agora são dinâmicos

---

## 📋 RESUMO EXECUTIVO

### 🎯 Objetivo do Projeto
Site de e-commerce para venda de camisetas do evento ONE WAY 2025, com sistema completo de pagamentos via Mercado Pago e gestão administrativa via Django.

### 🚀 Status Atual: **PRODUÇÃO ATIVA**
- ✅ **Frontend**: Funcionando em produção
- ✅ **Pagamentos**: Mercado Pago integrado com métodos dinâmicos
- ✅ **Gestão**: Django Admin operacional
- ✅ **Banco**: PostgreSQL Railway persistente

### 📊 Estatísticas Técnicas
- **Linhas de código**: 3.477+ core (HTML/CSS/JS) + 1.500+ Python + 2.117+ PayPal
- **Issues implementadas**: 21+ completas (#11-14, #17-19, #22-28, #39-44)
- **Issues planejadas**: 6 para sistema de estoque (#32-38)
- **Total issues**: 44+ criadas desde o início do projeto
- **Dependências**: Node.js 17MB otimizado, Python 15+ packages, PayPal SDK
- **Scripts**: test_db.py (125 linhas), server.js (1.300+ linhas), index.html (798 linhas)
- **Arquivos CSS**: style.css (2.048 linhas) + modais customizados
- **Pagamentos**: Sistema dual Mercado Pago + PayPal operacional

### 🔧 Tecnologias Utilizadas
- **Frontend**: HTML5, CSS3, JavaScript ES6+
- **Backend**: Node.js, Express.js
- **Admin**: Django, Django REST Framework
- **Banco**: PostgreSQL (Railway)
- **Pagamentos**: Mercado Pago API + PayPal REST API
- **Deploy**: Railway (auto-deploy)
- **Configuração**: Sistema dinâmico via variáveis de ambiente

### 💰 Produtos Configurados
- 4 tipos de camisetas (R$ 120,00 cada)
- Tamanhos: P, M, G, GG (com controle individual de estoque)
- Métodos: PIX (5% desconto), 2x sem juros, 4x com juros
- **Estoque atual**: Controlado via products.json
- **Estoque futuro**: Sistema automático Django + PostgreSQL (Issues #32-38)

---

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.