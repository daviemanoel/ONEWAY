# CLAUDE.md

Este arquivo fornece orientações para o Claude Code (claude.ai/code) ao trabalhar com código neste repositório.

## PRINCÍPIOS IMPORTANTES
- **SEMPRE responder em português brasileiro**
- Usar terminologia técnica em português quando possível
- Manter consistência com o idioma do projeto (site em português)

## Visão Geral do Projeto
Este é um site estático para o evento de conferência jovem "ONE WAY" (31 de julho - 2 de agosto de 2025). É uma aplicação de página única construída com HTML, CSS e JavaScript vanilla, com backend Node.js/Express para processamento de pagamentos.

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
- **Servidor local**: `node server.js` na porta 3000
- **Deploy**: Railway (https://oneway-production.up.railway.app)
- **Dependências**: `npm install` (express, cors, stripe, mercadopago, dotenv)
- **Variáveis ambiente**: STRIPE_SECRET_KEY, MERCADOPAGO_ACCESS_TOKEN

### Django Admin (Sistema de gestão)
- **Ambiente local**: `cd api && python manage.py runserver` (SQLite local)
- **Produção Railway**: PostgreSQL gerenciado com dados persistentes
- **Migrar localmente**: `python manage.py migrate`
- **Setup completo produção**: `python manage.py setup_database` (comando personalizado)
- **Admin produção**: https://api-production-e044.up.railway.app/admin/ (admin/oneway2025)
- **API Token**: `python manage.py create_api_token` (integração Node.js)
- **Consulta MP**: ⚠️ **EM DESENVOLVIMENTO** - Botão implementado mas com problemas de conectividade
- **Dependências**: Ver `api/requirements.txt`

### Comandos Úteis de Gestão
- **Testar API**: `curl -H "Authorization: Token SEU_TOKEN" https://api-production-e044.up.railway.app/api/pedidos/`
- **Reset DB local**: `rm db.sqlite3 && python manage.py migrate && python manage.py createsuperuser`
- **Logs produção**: `railway logs --service API`
- **Deploy forçado**: `railway up --service API`

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
- ✅ **Railway Deploy**: PostgreSQL persistente, dados preservados entre deploys
- ✅ **Comando personalizado**: setup_database para inicialização automática
- ✅ **Segurança**: Preços sempre vindos do servidor (products.json)
- ✅ **Admin funcional**: Links MP, consulta status, gestão completa

## FLUXO COMPLETO DE PAGAMENTO OTIMIZADO

### Sistema Atual Implementado ✅
**Objetivo ALCANÇADO**: Sistema completo de e-commerce com gestão de pedidos sem registros "fantasma".

#### Fluxo de Pagamento Seguro:
```
1. Cliente preenche formulário (nome, email, telefone)
2. Seleciona produto + tamanho + forma de pagamento
3. Clica "Pagar" → Cria preferência MP (SEM registro no banco)
4. Redireciona para Mercado Pago
5. Cliente paga no MP
6. MP redireciona para mp-success.html COM dados do comprador na URL
7. Página detecta status=approved → Cria registros automaticamente
8. Exibe confirmação visual + ID do pedido
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

#### Próximas Implementações:
- ⚠️ **URGENTE: Fix botão Consultar MP** - Resolver conectividade com API MP
- **Issue #15**: Webhook MP para automação total (não crítico)
- **Relatórios**: Dashboard de vendas e métricas
- **Notificações**: Email automático para compradores
- **Estoque**: Controle automático de quantidades

#### Problemas Conhecidos:
- ❌ **Botão "Consultar Status MP"**: Implementado com JavaScript, CSS e endpoint Django, mas não está funcionando em produção
  - Código completo em: `api/pedidos/static/admin/js/consultar_mp.js`
  - Endpoint: `/consultar-mp/` com autenticação staff_member_required
  - Token MP configurado no Railway
  - Precisa investigar logs detalhados e debugging

#### Arquitetura Final Implementada:
```
[Frontend HTML/JS] → [Node.js/Express] → [Mercado Pago]
                            ↓
                    [Django REST API] → [PostgreSQL Railway]
                            ↓
                    [Admin Interface] → [Gestão Completa]
```

## Observações Técnicas Importantes

### Deploy e Banco de Dados
- **PostgreSQL Railway**: Banco persistente, dados nunca são perdidos entre deploys
- **Comando setup_database**: Criação automática de tabelas Django + superuser admin/oneway2025
- **WhiteNoise**: Serve arquivos estáticos CSS/JS do Django Admin corretamente
- **Variável DATABASE_URL**: Auto-detecta PostgreSQL em produção, SQLite local

### Frontend e UX
- **JavaScript inline**: Todo código JS está no index.html (500+ linhas)
- **Lazy loading**: Imagens otimizadas exceto hero banner
- **Mobile-first**: Breakpoint principal 768px, design responsivo completo
- **Conversão JPEG**: Compatibilidade Linux (case-sensitive)

## Configurações de Produção

### Variáveis de Ambiente Necessárias
```bash
# Node.js (Railway Web Service)
MERCADOPAGO_ACCESS_TOKEN=APP_USR_xxx  # Token produção MP
DJANGO_API_URL=https://api-production-e044.up.railway.app/api
DJANGO_API_TOKEN=xxx  # Token gerado pelo Django
MP_SUCCESS_URL=https://oneway-production.up.railway.app/mp-success
MP_CANCEL_URL=https://oneway-production.up.railway.app/mp-cancel

# Django (Railway API Service)  
DATABASE_URL=postgresql://xxx  # Auto-configurado pelo Railway
DJANGO_SECRET_KEY=xxx
DEBUG=False
MERCADOPAGO_ACCESS_TOKEN=APP_USR_xxx  # Para consultas admin
```

### Segurança Implementada
- ✅ **Preços protegidos**: Sempre vindos do products.json servidor
- ✅ **Token API**: Autenticação segura Django ↔ Node.js
- ✅ **CORS configurado**: Apenas domínios autorizados
- ✅ **Logs anti-fraude**: Detecção de tentativas de manipulação
- ✅ **Validação dupla**: Frontend + backend + Django
- ✅ **PostgreSQL**: Banco persistente e seguro

### Limitações Conhecidas (Menores)
- Cliente pode alterar método no checkout MP (preço permanece correto)
- Links MP admin podem precisar ajuste conforme painel MP
- Checkout sem login MP (trade-off: UX vs conversão)
- Stripe mantido no código (legacy, não usado)

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.