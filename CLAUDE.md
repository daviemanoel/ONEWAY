# CLAUDE.md

Este arquivo fornece orientações para o Claude Code (claude.ai/code) ao trabalhar com código neste repositório.

## PRINCÍPIOS IMPORTANTES
- **SEMPRE responder em português brasileiro**
- Usar terminologia técnica em português quando possível
- Manter consistência com o idioma do projeto (site em português)

## Visão Geral do Projeto
Este é um site estático para o evento de conferência jovem "ONE WAY" (31 de julho - 2 de agosto de 2025). É uma aplicação de página única construída com HTML, CSS e JavaScript vanilla.

## Comandos de Desenvolvimento
Como este é um site estático sem processo de build:
- **Rodar localmente**: Abra `index.html` diretamente no navegador ou use um servidor local como `python -m http.server 8000` ou `npx serve`
- **Sem comandos de build/lint/teste** - É puro HTML/CSS/JS sem ferramentas

## Arquitetura e Componentes Principais

### Estrutura de Arquivos
- `index.html` - Página única contendo todo o conteúdo (383 linhas)
- `Css/style.css` - Todos os estilos em um arquivo (1655 linhas)
- `img/` - Assets organizados: `img/camisetas/`, `img/ingressos/`, imagens gerais
- `products.json` - Base de dados dos produtos com integração Stripe

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

### Sistema de Produtos Dinâmicos (Novo)
- **products.json** contém 4 camisetas com configuração completa por tamanho
- Carregamento via JavaScript assíncrono com função `loadProducts()`
- Integração direta com Stripe via links específicos por produto/tamanho
- Seleção de tamanhos com botões interativos (P, M, G, GG)
- Grid responsivo: 4 colunas desktop → 1 coluna mobile (vertical)
- Preços e disponibilidade controlados via JSON

### Sistema de Navegação e Layout
- **Header fixo** com efeito blur e transparência ao rolar
- **Smooth scroll** entre seções com âncoras
- **Menu hamburger** responsivo para mobile com auto-close
- **Layout tabela** para seção ingressos (Date + Tickets combinados)
- **Breakpoint principal**: 768px para mobile/desktop

### Integração de Pagamentos
- **Ingressos**: tiketo.com.br (links diretos, 3 lotes ativos)
- **Produtos**: Stripe com links por tamanho específico
- **Fallback**: Redirecionamento para tiketo quando Stripe indisponível
- **Validação**: Seleção obrigatória de tamanho antes da compra

### Status da Integração de Pagamento
- Vendas de ingressos externas gerenciadas por tiketo.com.br
- Sistema de produtos com Stripe implementado (internacional, sem parcelamento)
- Mercado Pago em desenvolvimento (PIX + parcelamento 2x sem juros, até 12x com juros)
- Lote 4 comentado (não disponível para venda)
- Headers de segurança configurados em meta tags

### Issues Ativas - Mercado Pago
- Issue #6: Setup backend e dependências MP
- Issue #7: Endpoint checkout com parcelamento  
- Issue #8: Frontend dual payment (Stripe + MP)
- Issue #9: Páginas success/cancel Mercado Pago
- Issue #10: Testes e validação end-to-end

## Observações Importantes
- Todo JavaScript está inline no index.html (381 linhas) - sem arquivos JS separados
- Imagens otimizadas com lazy loading (exceto hero banner)
- Sem variáveis de ambiente ou arquivos de configuração
- Design responsivo completo com mobile-first approach
- FAQ interativo com 10 perguntas em accordion

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.