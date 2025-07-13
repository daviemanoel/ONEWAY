# CLAUDE.md

Este arquivo fornece orientações para o Claude Code (claude.ai/code) ao trabalhar com código neste repositório.

## PRINCÍPIOS IMPORTANTES
- **SEMPRE responder em português brasileiro**
- Usar terminologia técnica em português quando possível
- Manter consistência com o idioma do projeto (site em português)

## Visão Geral do Projeto
Este é um site estático para o evento de conferência jovem "ONE WAY" (31 de julho - 2 de agosto de 2025). É uma aplicação de página única construída com HTML, CSS e JavaScript vanilla, com backend Node.js/Express para processamento de pagamentos.

## Comandos de Desenvolvimento
### Frontend (Site estático)
- **Rodar localmente**: Abra `index.html` diretamente no navegador ou use um servidor local como `python -m http.server 8000` ou `npx serve`
- **Sem comandos de build/lint/teste** - É puro HTML/CSS/JS sem ferramentas

### Backend (Processamento de pagamentos)
- **Servidor local**: `node server.js` na porta 3000
- **Deploy**: Railway (https://oneway-production.up.railway.app)
- **Dependências**: `npm install` (express, cors, stripe, mercadopago, dotenv)
- **Variáveis ambiente**: STRIPE_SECRET_KEY, MERCADOPAGO_ACCESS_TOKEN

## Arquitetura e Componentes Principais

### Estrutura de Arquivos
- `index.html` - Página única contendo todo o conteúdo (507 linhas)
- `Css/style.css` - Todos os estilos em um arquivo (1655+ linhas)
- `server.js` - Backend Node.js/Express para pagamentos (212 linhas)
- `products.json` - Base de dados dos produtos com preços e estoque
- `img/` - Assets organizados: `img/camisetas/`, `img/ingressos/`, imagens gerais
- `mp-success.html` / `mp-cancel.html` - Páginas de retorno Mercado Pago
- `success.html` / `cancel.html` - Páginas de retorno Stripe
- `package.json` - Dependências do backend

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

### Integração de Pagamentos
- **Ingressos**: tiketo.com.br (links diretos, 3 lotes ativos)
- **Produtos**: Mercado Pago via backend Node.js/Express
- **Fluxo**: Frontend → Backend `/create-mp-checkout` → Mercado Pago Checkout
- **Validação**: Seleção obrigatória de tamanho e forma de pagamento

### Sistema de Pagamento Atual (Mercado Pago)
- **PIX**: 5% de desconto (R$ 114,00)
- **Cartão**: Até 2x sem juros, até 4x com juros (R$ 120,00)
- **Backend**: Express.js com endpoints dedicados
- **Segurança**: Variáveis de ambiente no Railway
- **Checkout**: Simplificado sem exigência de login MP
- **Retorno**: Páginas success/cancel dedicadas

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

## ROADMAP - Sistema de Gestão de Pedidos

### Próximas Implementações (Issues GitHub)
**Objetivo**: Criar sistema admin Django para gestão completa de pedidos e dados de compradores.

#### Issues Criadas:
1. **[#11 - Capturar dados MP na página sucesso](https://github.com/daviemanoel/ONEWAY/issues/11)** 🎯
   - Implementar captura de `payment_id`, `status`, `external_reference` do Mercado Pago
   - Modificar `mp-success.html` para extrair parâmetros da URL
   - Base para integração com sistema admin

2. **[#12 - Admin Django para gestão pedidos](https://github.com/daviemanoel/ONEWAY/issues/12)** 🛠️
   - Criar models: Comprador (nome, email, telefone) e Pedido (produto, pagamento, status)
   - Interface Django Admin completa com filtros e buscas
   - Controle manual de status (Pago/Pendente/Cancelado)

3. **[#13 - API comunicação Node.js ↔ Django](https://github.com/daviemanoel/ONEWAY/issues/13)** 🔗
   - REST API para sincronizar dados entre sistemas
   - Endpoints: criar pedido, atualizar status, consultar MP
   - Autenticação por token API

4. **[#14 - Formulário dados comprador](https://github.com/daviemanoel/ONEWAY/issues/14)** 📝
   - Modal/seção checkout com campos: nome, email, telefone
   - Validação JavaScript e UX responsiva
   - Fluxo: dados → Django → redirect MP

5. **[#15 - Webhook Mercado Pago](https://github.com/daviemanoel/ONEWAY/issues/15)** 🔄
   - Automação: receber notificações MP para atualizar status
   - Implementação futura (não crítico para MVP)

#### Arquitetura Planejada:
```
[Site Node.js] ← API REST → [Admin Django] ← Webhook → [Mercado Pago]
     ↓                           ↓                         ↓
[Frontend]                 [Gestão Pedidos]           [Pagamentos]
```

#### Ordem de Implementação:
`#11 (Base)` → `#12 (Admin)` → `#13 (API)` → `#14 (UX)` → `#15 (Automação)`

## Observações Técnicas Importantes
- Todo JavaScript está inline no index.html (500+ linhas) - sem arquivos JS separados
- Imagens otimizadas com lazy loading (exceto hero banner)
- Backend usa variáveis de ambiente para chaves API (Railway)
- Design responsivo completo com mobile-first approach
- FAQ interativo com 10 perguntas em accordion
- Conversão PNG→JPEG para compatibilidade Linux (case-sensitive)

## Limitações Conhecidas
- Desconto PIX é aplicado no backend, mas cliente pode trocar método no checkout MP
- Não há captura detalhada de dados do comprador (email, telefone)
- Checkout sem login pode reduzir conversão mas melhora UX
- Stripe mantido no código mas não utilizado no fluxo atual

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.