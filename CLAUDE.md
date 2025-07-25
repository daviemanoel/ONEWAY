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
        ↓                    ↓                     ↓
[products.json]    [Django REST API] → [PostgreSQL Railway]
        ↓                    ↓                     ↓ 
[Cache 5min]   [Admin Interface + Presencial] → [Gestão Completa]
```

### Status: 🚀 **PRODUÇÃO ATIVA**
- ✅ **Frontend**: https://oneway.mevamfranca.com.br
- ✅ **Admin Django**: https://api.oneway.mevamfranca.com.br/admin (admin/oneway2025)
- ✅ **Pagamentos**: Mercado Pago + PayPal + Presencial
- ✅ **Banco**: PostgreSQL Railway persistente
- ✅ **Carrinho**: Sistema completo de múltiplos itens
- ✅ **Controle de Estoque**: Sistema automático em tempo real ⭐ **NOVO**
- ✅ **Pagamento Presencial**: Estoque decrementado imediatamente ⭐ **NOVO**

## Comandos de Desenvolvimento

### 🎯 Dashboard Administrativo Centralizado ⭐ **NOVO**
```bash
# Acesso ao dashboard completo
URL: https://api.oneway.mevamfranca.com.br/api/setup-estoque/
Login: Requer autenticação como staff member (@staff_member_required)

# Funcionalidades disponíveis via interface web AJAX:
- 🔄 Reset Completo do Estoque (restaura valores originais)
- 📦 Sincronizar Estoque (processa pedidos aprovados)
- 🚀 Setup Inicial (configura produtos)
- 📄 Gerar Products.json (atualiza frontend)
- 🔗 Associar Pedidos Legacy (migração dados)
- 🔑 Criar Token API (comunicação Node.js)
- 🔍 Simulações --dry-run (testes sem alterações)

# Estatísticas em tempo real:
- Produtos esgotados (estoque = 0)
- Estoque baixo (< 2 unidades) ⭐ **NOVO THRESHOLD**
- Pedidos pendentes de processamento
- Pagamentos presenciais aguardando confirmação
```

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

# Comandos customizados ⭐ **ATUALIZADOS - JANEIRO 2025**
python manage.py setup_estoque_simples     # Setup automático produção
python manage.py reset_estoque --confirmar # Reset completo estoque ⭐ **NOVO**
python manage.py sincronizar_estoque       # Sincronizar estoque (30 dias padrão)
python manage.py sincronizar_estoque --reprocessar # Incluir pedidos já processados ⭐ **NOVO**
python manage.py gerar_products_json       # Gerar JSON atualizado
python manage.py associar_pedidos_legacy   # Migração dados
python manage.py criar_token_api          # Gerar token para Node.js

# Comandos de diagnóstico ⭐ **JANEIRO 2025**
python manage.py verificar_movimentacoes 76    # Analisar movimentações pedido específico
python manage.py testar_movimentacoes 76 --forcar # Forçar criação movimentações para teste

# Comandos com dry-run (simulação)
python manage.py reset_estoque --dry-run        # Simular reset
python manage.py sincronizar_estoque --dry-run  # Simular sincronização
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
├── web/                       # Frontend + Backend Node.js
│   ├── index.html            # SPA com carrinho + presencial (1550+ linhas)
│   ├── Css/style.css         # Sistema design + carrinho (2400+ linhas)
│   ├── server.js             # Backend + APIs completas (1480+ linhas)
│   ├── products.json         # Base dados produtos
│   ├── mp-success.html       # Página retorno Mercado Pago
│   ├── paypal-success.html   # Página retorno PayPal
│   ├── presencial-success.html # Página confirmação presencial
│   └── img/                  # Assets organizados (JPEG)
└── api/                      # Django Admin System
    ├── oneway_admin/         # Configurações Django
    ├── pedidos/              # App principal (models, admin, serializers)
    │   ├── models.py         # Pedido + ItemPedido + Presencial
    │   ├── admin.py          # Interface + action presencial
    │   └── migrations/       # Inclui migração de dados
    ├── manage.py             # Django CLI
    └── requirements.txt      # Dependências Python
```

### Sistema de Pagamentos Dinâmico

O sistema suporta múltiplos provedores através de configuração dinâmica:

**Variáveis de Ambiente (Railway):**
```bash
FORMA_PAGAMENTO_CARTAO=MERCADOPAGO  # ou PAYPAL
FORMA_PAGAMENTO_PIX=MERCADOPAGO     # sempre MP (PIX exclusivo)
# Pagamento presencial sempre disponível (sem configuração externa)
```

**Fluxo de Pagamento:**
1. Cliente adiciona produtos ao carrinho
2. Carrinho persiste com localStorage
3. Ícone flutuante mostra contador de itens
4. Painel lateral para gerenciar quantidades
5. Seleção de método de pagamento no carrinho:
   - **PIX** → Mercado Pago (5% desconto)
   - **Cartão** → Mercado Pago ou PayPal (dinâmico)
   - **Presencial** → Reserva com confirmação na igreja ⭐ **NOVO**
6. Modal coleta dados (nome, email, telefone)
7. Sistema roteia conforme método escolhido
8. Página de retorno/confirmação cria pedido no Django
9. Admin permite gestão completa + confirmação presencial

### Models Django Principais

**Comprador:**
- nome, email, telefone, data_cadastro

**Pedido:**
- Relacionamento 1:N com Comprador
- produto (4 camisetas), tamanho (P,M,G,GG), preco (legado)
- forma_pagamento (pix, 2x, 4x, paypal, presencial, etc.) ⭐ **NOVO**
- external_reference (único), payment_id, preference_id
- status_pagamento (pending, approved, rejected, etc.)
- Logs completos com timestamps
- Método total_pedido calcula valor baseado nos itens
- Action admin para confirmação presencial ⭐ **NOVO**

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
- **Carrinho abre automaticamente ao adicionar produto** ⭐ **NOVO**
- **Link "Escolher outros modelos" para continuar comprando** ⭐ **NOVO**

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

**Melhorias de UX:** ⭐ **JANEIRO 2025**
- Ao adicionar produto, o painel do carrinho abre automaticamente
- Link "Escolher outros modelos" abaixo do botão de finalizar compra
- Navegação suave de volta para a seção de produtos
- Correção de timing na inicialização do carrinho
- Event listeners otimizados sem duplicação

**Correção Sincronização Estoque:** ⭐ **JANEIRO 2025**
- Fix crítico na lógica de exclusão de pedidos com ItemPedido
- Comando `--reprocessar` para incluir pedidos já processados
- Auto-associação de ItemPedido via campos legacy quando produto_tamanho é null
- Comandos de diagnóstico para debug de movimentações específicas
- Dashboard com logs persistentes (não fecha automaticamente)

### Sistema de Pagamento Presencial ⭐ **NOVO**

Sistema completo para reserva e pagamento na igreja implementado:

**Frontend (JavaScript):**
- Opção "Pagamento Presencial" no seletor de métodos
- Modal específico com instruções detalhadas
- Avisos sobre prazo de 48h para confirmação
- Validação obrigatória de dados pessoais
- Integração total com carrinho de múltiplos itens

**Backend (Node.js):**
- Endpoint `/api/cart/checkout-presencial` dedicado
- Criação automática de pedidos com status "pending"
- Geração de external_reference único para rastreamento
- Validação de preços e disponibilidade
- Logs detalhados para auditoria administrativa

**Django Admin:**
- Action "Confirmar Pagamento Presencial" para staff
- Filtro específico "Pedidos Presenciais Pendentes"
- Mudança automática pending → approved
- Interface integrada com sistema ItemPedido
- Controle completo de confirmações

**Fluxo Completo:**
1. Cliente seleciona "Pagamento Presencial" no carrinho
2. Sistema gera pedido com status "pending" 
3. Cliente recebe número do pedido na página de confirmação
4. Cliente vai na igreja em até 48h com o número
5. Staff confirma pagamento via Django Admin
6. Status muda automaticamente para "approved"

**Benefícios:**
- ✅ Zero taxas de gateway de pagamento
- ✅ Alternativa confiável ao PayPal problemático
- ✅ Atende membros que preferem pagamento físico
- ✅ Mantém relacionamento presencial igreja-membro
- ✅ Controle administrativo total via Django

### Sistema de Controle de Estoque Completo ⭐ **NOVO**

Sistema integrado de controle de estoque com histórico completo de movimentações implementado:

**🏗️ Arquitetura:**
```
[Frontend] → [product_size_id] → [Node.js] → [Django API] → [PostgreSQL]
     ↓              ↓               ↓            ↓             ↓
[products.json] → [Validação] → [Sincronização] → [Models] → [Histórico]
```

**📊 Models Django:**
- **Produto**: Gestão de produtos com preço, custo, ordem, ativo
- **ProdutoTamanho**: Controle de estoque por tamanho (P/M/G/GG)
- **MovimentacaoEstoque**: Histórico completo de todas as movimentações
- **Pedido**: Integração híbrida (novo sistema + legacy)
- **ItemPedido**: Suporte a múltiplos itens por pedido

**🔄 Sincronização Automática:**
- **Dashboard Web**: `/api/setup-estoque/` com interface visual
- **Comando CLI**: `python manage.py sincronizar_estoque`
- **Admin Actions**: Sincronização direta no Django Admin
- **Híbrido**: Processa pedidos novos + legacy automaticamente
- **Pedidos Presenciais**: Incluídos automaticamente na sincronização
- **Histórico**: Todas as movimentações registradas com pedido relacionado

**📈 Funcionalidades Avançadas:**
- **Reset de Estoque**: Comando para reprocessamento completo
- **Migração de Dados**: Scripts automáticos products.json → Django
- **Validação Dupla**: Frontend + Backend + Django
- **Dry-run Mode**: Simulação sem alterar dados
- **Geração JSON**: products.json atualizado automaticamente
- **Logs Detalhados**: Auditoria completa de todas as operações
- **Diagnóstico**: Comandos para debug de pedidos específicos ⭐ **JANEIRO 2025**
- **Auto-recuperação**: Lookup automático de ProdutoTamanho via legacy fields ⭐ **JANEIRO 2025**

**🎯 Interface Admin:**
- **Produtos**: Lista com estoque total, margem de lucro, status visual
- **Tamanhos**: Edição inline com botões de ação rápida (+5/-1)
- **Histórico**: Visualização completa de movimentações por produto
- **Filtros**: Por tipo, data, usuário, origem da movimentação
- **Actions**: Sincronizar estoque, confirmar presencial, gerar JSON

**💻 Dashboard Centralizado:**
```
https://api.oneway.mevamfranca.com.br/api/setup-estoque/
```
- 📊 Estatísticas em tempo real (esgotados, baixo estoque, pendentes)
- 🔄 Botões de comando (Reset, Sincronizar, Gerar JSON)
- 📋 Logs de execução via AJAX (persistentes até fechar manualmente) ⭐ **JANEIRO 2025**
- 🔐 Autenticação obrigatória (@staff_member_required)
- 📱 Interface responsiva e moderna
```

**Models Django:**
```python
class ProdutoTamanho(models.Model):
    produto = models.ForeignKey(Produto, related_name='tamanhos')
    tamanho = models.CharField(max_length=5)
    estoque = models.IntegerField(default=0)
    disponivel = models.BooleanField(default=True)
    
    def decrementar_estoque(self, quantidade=1):
        """Decrementa estoque e atualiza disponibilidade"""
        if self.estoque >= quantidade:
            self.estoque -= quantidade
            if self.estoque == 0:
                self.disponivel = False
            self.save()
            return True
        return False
    
    def incrementar_estoque(self, quantidade=1):
        """Incrementa estoque e reativa produto se necessário"""
        if quantidade > 0:
            self.estoque += quantidade
            if not self.disponivel and self.estoque > 0:
                self.disponivel = True
            self.save()
            return True
        return False
```

**Integração Frontend:**
- ✅ Botões de tamanho incluem `data-product-size-id`
- ✅ Carrinho armazena IDs numéricos do Django
- ✅ Validação em tempo real antes do checkout
- ✅ Migração automática de carrinhos antigos

**APIs REST:**
```bash
POST /api/estoque-multiplo/        # Validar múltiplos itens
POST /api/decrementar-estoque/     # Decrementar imediato (presencial)
GET  /api/validar-estoque/         # Validar item único
```

**Pagamento Presencial Automático:**
1. **Cliente seleciona "Presencial"** → Validação de estoque
2. **🔥 ESTOQUE DECREMENTADO IMEDIATAMENTE** → Reserva confirmada
3. **Pedido criado com `pending`** → Aguarda pagamento igreja
4. **Admin confirma** → Status muda para `approved`

**Cancelamento com Devolução:**
1. **Admin cancela pedido** → Action "Cancelar e devolver estoque"
2. **Sistema verifica `estoque_decrementado=True`** → Devolve automaticamente
3. **Estoque restaurado** → Produto disponível novamente

**Benefícios:**
- ✅ **Zero overselling**: Reserva imediata de estoque
- ✅ **Sistema reversível**: Cancelamentos devolvem estoque
- ✅ **Tempo real**: Validação instantânea
- ✅ **Transações atômicas**: Consistência garantida
- ✅ **Logs detalhados**: Auditoria completa

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
- ✅ **Issues #1-14, #17-28**: Fluxo Mercado Pago completo + infraestrutura
- ✅ **Issues #39-44**: Integração PayPal com configuração dinâmica
- ✅ **Issues #46-53**: Sistema carrinho de compras completo
- ✅ **Issue #45**: Pagamento presencial na igreja implementado
- ✅ **Issues #32-37**: Sistema controle estoque Django COMPLETO ⭐ **NOVO**
  - ✅ **#32**: Refactor sistema controle estoque com models Django
  - ✅ **#33**: Models Produto e ProdutoTamanho criados
  - ✅ **#34**: Scripts migração products.json → Django
  - ✅ **#35**: Interface admin completa para produtos e estoque
  - ✅ **#36**: Comando sincronização híbrido (novo + legacy)
  - ✅ **#37**: Frontend integrado com IDs numéricos Django
- ✅ **Janeiro 2025**: Correções críticas sincronização + diagnóstico ⭐ **NOVO**
  - ✅ **Fix lógica exclusão**: Pedidos com ItemPedido não eram processados corretamente
  - ✅ **Auto-lookup**: ItemPedido sem produto_tamanho agora usa campos legacy
  - ✅ **Comando --reprocessar**: Incluir pedidos já decrementados na sincronização
  - ✅ **Comandos diagnóstico**: verificar_movimentacoes e testar_movimentacoes
  - ✅ **Dashboard logs**: Logs permanecem visíveis até fechamento manual

### Sessão 24-25 Julho 2025: Sistema de Alimentação e Validação de Produtos Inativos ⭐ **NOVO**

#### Contexto da Sessão
**Objetivo inicial**: Adicionar área de compra de alimentação (almoço e jantar sábado) no site

#### Issues Resolvidas:
- ✅ **Issue #54**: Sistema de alimentação implementado
  - ✅ HTML: Seção "Alimentação do Evento" com cards de almoço/jantar
  - ✅ CSS: Design responsivo com gradientes e hover effects  
  - ✅ JavaScript: Integração com carrinho existente
  - ✅ Backend: Suporte a produtos com tamanho UNICO
  - ✅ Products.json: Produtos ID 5 (almoço) e 6 (jantar) adicionados

- ✅ **Issue #55**: Django Admin - Suporte a produtos de alimentação
  - ✅ Models: PRODUTOS_CHOICES expandido com almoco-sabado e jantar-sabado
  - ✅ Models: TAMANHOS_CHOICES expandido com UNICO
  - ✅ Migração: 0007_adicionar_produtos_alimentacao.py criada
  - ✅ Comando migrar_produtos: Cadastro automático via dashboard

- ✅ **Issue #56**: Validação de produto ativo no sistema
  - ✅ Models: Método esta_disponivel agora valida produto.ativo
  - ✅ Backend: Produtos inativos ficam indisponíveis automaticamente
  - ✅ Command: gerar_products_json inclui produtos inativos (marked as unavailable)
  - ✅ Frontend: Botões desabilitados para produtos sem tamanhos disponíveis

#### Problemas Encontrados e Soluções:

**🚨 Problema 1: Erro "UNICO não é escolha válida"**
- **Causa**: Django não aceitava tamanho UNICO (só P,M,G,GG)
- **Fix temporário**: Mudar para tamanho G no admin e frontend
- **Fix definitivo**: Adicionar UNICO nas TAMANHOS_CHOICES

**🚨 Problema 2: Erro "almoco-sabado não é escolha válida"**  
- **Causa**: Django só aceitava 4 camisetas nas PRODUTOS_CHOICES
- **Fix temporário horrível**: Mapear alimentação para camiseta-marrom no server.js
- **Fix definitivo**: Adicionar produtos alimentação nas PRODUTOS_CHOICES

**🚨 Problema 3: Frontend não respeitava produto inativo**
- **Causa**: gerar_products_json filtrava apenas produtos ativos
- **Fix**: Incluir todos produtos, usar esta_disponivel para marcar disponibilidade

**🚨 Problema 4: Botões alimentação permaneciam azuis (não implementado completamente)**
- **Tentativa 1**: Lógica de verificação de disponibilidade (falhou)
- **Tentativa 2**: Função updateMealButtons() dinâmica (falhou)  
- **Solução temporária**: `display: none` nos botões .meal-btn

#### Estado Atual (24/07/2025 23:20):

**✅ Funcionando:**
- Sistema de alimentação HTML/CSS completo
- Carrinho suporta múltiplos produtos + alimentação  
- Django aceita produtos de alimentação (almoco-sabado, jantar-sabado)
- Django aceita tamanho UNICO
- Produtos inativos ficam indisponíveis no sistema
- Validação completa de produto.ativo

**❌ Pendente para amanhã:**
- **Botões de alimentação desabilitados quando produto inativo**
  - Botões estão escondidos (display: none) temporariamente
  - Precisa implementar corretamente a lógica de updateMealButtons()
  - Verificar por que função não funcionou conforme esperado

#### Arquivos Modificados na Sessão:
```
web/products.json - Produtos alimentação adicionados
web/index.html - Seção alimentação + fallback dados + updateMealButtons()
web/Css/style.css - Estilos alimentação + botões desabilitados + display: none
web/server.js - Hack temporário removido (camiseta-marrom mapping)
api/pedidos/models.py - PRODUTOS_CHOICES + TAMANHOS_CHOICES + esta_disponivel
api/pedidos/management/commands/gerar_products_json.py - Incluir produtos inativos
api/pedidos/migrations/0007_adicionar_produtos_alimentacao.py - Migração choices
```

#### Próximos Passos (Para Amanhã):
1. **Debug função updateMealButtons()**: Verificar por que não funcionou
2. **Remover display: none**: Implementar lógica correta de desabilitação
3. **Testar produtos inativos**: Confirmar que sistema funciona end-to-end
4. **Considerar UX**: Melhor feedback visual para produtos indisponíveis

### Metodologia Issues
- **code-complete**: Código implementado, mas não testado
- **testing**: Em fase de testes
- **validated**: Testado e funcionando
- **closed**: Entregue e validado

### Problemas Conhecidos
- ❌ **Botão "Consultar Status MP"**: Implementado mas não funcional
- ⚠️ **PayPal guest checkout**: Pode forçar criação conta (limitação API)
- ⚠️ **Pagamento presencial**: Pedidos não confirmados em 48h ficam pendentes (manual)

## Tecnologias e Dependências

**Frontend:** HTML5, CSS3, JavaScript ES6+ (vanilla)  
**Backend:** Node.js 18+, Express.js  
**Admin:** Django 5.2.4, Django REST Framework 3.16.0  
**Banco:** PostgreSQL (Railway), SQLite (local)  
**Pagamentos:** Mercado Pago API, PayPal REST API  
**Deploy:** Railway (auto-deploy, custom domains)  

**Estatísticas:**
- ~12000+ linhas código total (HTML/CSS/JS + Python)
- 53 issues criadas → **46 fechadas com sucesso** ✅ (87% conclusão)
- Sistema completo: **Pagamentos (MP + PayPal + Presencial) + Controle Estoque**
- PostgreSQL persistente com zero downtime
- **Sistema híbrido**: Novo + Legacy funcionando simultaneamente
- **Histórico completo**: MovimentacaoEstoque com 520+ linhas de código
- **Dashboard admin**: Interface moderna com 15+ comandos
- **100% funcionalidades carrinho + presencial + estoque implementadas** ⭐

---

## Lembrete Final

**O sistema está em PRODUÇÃO ATIVA** servindo clientes reais. Sempre teste mudanças localmente e use logs detalhados para debugging. Railway faz deploy automático - cuidado com commits diretos na main.