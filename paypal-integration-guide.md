# Guia de Integração PayPal para ONEWAY

## Resumo Executivo

Este documento apresenta uma proposta de integração do PayPal como **método adicional** de pagamento (não substituto do Mercado Pago).

## Por que adicionar PayPal?

### Vantagens:
- 📈 **Aumentar conversão**: Alguns clientes preferem PayPal
- 🌍 **Clientes internacionais**: PayPal é mais conhecido globalmente
- 🔒 **Percepção de segurança**: Proteção ao comprador PayPal
- 💳 **Suporte amplo de cartões**: Visa, Master, Amex, Hiper, Elo
- 💰 **Parcelamento flexível**: De 2x a 12x

### Desvantagens:
- ❌ **Sem PIX**: Perdeu suporte em 2023
- 👤 **Conta obrigatória**: Cliente precisa ter/criar conta PayPal
- 💸 **Taxas maiores**: ~5% por transação vs ~3% Mercado Pago
- 📉 **Menor adoção Brasil**: Menos popular que Mercado Pago

## Implementação Proposta

### 1. Instalar SDK PayPal
```bash
cd web
npm install @paypal/checkout-server-sdk
```

### 2. Adicionar Endpoint no server.js
```javascript
// Configurar PayPal
const paypal = require('@paypal/checkout-server-sdk');

const payPalClient = new paypal.core.PayPalHttpClient(
  process.env.PAYPAL_SANDBOX === 'true' 
    ? new paypal.core.SandboxEnvironment(
        process.env.PAYPAL_CLIENT_ID,
        process.env.PAYPAL_CLIENT_SECRET
      )
    : new paypal.core.LiveEnvironment(
        process.env.PAYPAL_CLIENT_ID,
        process.env.PAYPAL_CLIENT_SECRET
      )
);

// Endpoint para criar ordem PayPal
app.post('/create-paypal-order', async (req, res) => {
  try {
    const { productName, size, nome, email, telefone } = req.body;
    
    // Buscar preço seguro do products.json
    const productsData = getProductsCatalog();
    const product = Object.values(productsData.products)
      .find(p => p.title === productName);
    
    if (!product) {
      return res.status(400).json({ error: 'Produto não encontrado' });
    }
    
    const request = new paypal.orders.OrdersCreateRequest();
    request.prefer("return=representation");
    request.requestBody({
      intent: 'CAPTURE',
      purchase_units: [{
        amount: {
          currency_code: 'BRL',
          value: product.price.toFixed(2)
        },
        description: `${productName} - Tamanho ${size}`
      }],
      application_context: {
        brand_name: 'ONE WAY 2025',
        locale: 'pt-BR',
        landing_page: 'NO_PREFERENCE',
        shipping_preference: 'NO_SHIPPING',
        user_action: 'PAY_NOW',
        return_url: `${process.env.BASE_URL}/paypal-success`,
        cancel_url: `${process.env.BASE_URL}/paypal-cancel`
      }
    });
    
    const order = await payPalClient.execute(request);
    
    // Criar pedido pendente no Django
    const pedidoData = {
      nome,
      email,
      telefone,
      produto: mapearProdutoParaId(productName),
      tamanho: size,
      preco: product.price,
      forma_pagamento: 'paypal',
      status_pagamento: 'pending',
      external_reference: order.result.id
    };
    
    await axios.post(`${DJANGO_API_URL}/pedidos/`, pedidoData, {
      headers: {
        'Authorization': `Token ${DJANGO_API_TOKEN}`,
        'Content-Type': 'application/json'
      }
    });
    
    res.json({
      id: order.result.id,
      approval_url: order.result.links.find(link => link.rel === 'approve').href
    });
    
  } catch (error) {
    console.error('Erro PayPal:', error);
    res.status(500).json({ error: 'Erro ao criar ordem PayPal' });
  }
});

// Capturar pagamento após aprovação
app.post('/capture-paypal-order', async (req, res) => {
  try {
    const { orderID } = req.body;
    
    const request = new paypal.orders.OrdersCaptureRequest(orderID);
    request.requestBody({});
    
    const capture = await payPalClient.execute(request);
    
    // Atualizar status no Django
    if (capture.result.status === 'COMPLETED') {
      await axios.post(
        `${DJANGO_API_URL}/pedidos/referencia/${orderID}/atualizar_status/`,
        {
          status_pagamento: 'approved',
          payment_id: capture.result.id
        },
        {
          headers: {
            'Authorization': `Token ${DJANGO_API_TOKEN}`,
            'Content-Type': 'application/json'
          }
        }
      );
    }
    
    res.json({ status: capture.result.status });
    
  } catch (error) {
    console.error('Erro ao capturar pagamento:', error);
    res.status(500).json({ error: 'Erro ao processar pagamento' });
  }
});
```

### 3. Adicionar Botão PayPal no Frontend

No modal de checkout (index.html):
```javascript
// Adicionar opção PayPal no seletor de pagamento
<label class="payment-option">
  <input type="radio" name="payment_method" value="paypal">
  <div class="payment-content">
    <strong>PayPal</strong>
    <small>Cartão ou saldo PayPal</small>
  </div>
</label>

// Função para checkout PayPal
async function processarPagamentoPayPal(productData) {
  try {
    const response = await fetch('/create-paypal-order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        productName: productData.name,
        size: productData.size,
        nome: document.getElementById('nome').value,
        email: document.getElementById('email').value,
        telefone: document.getElementById('telefone').value
      })
    });
    
    const order = await response.json();
    
    // Redirecionar para PayPal
    window.location.href = order.approval_url;
    
  } catch (error) {
    console.error('Erro:', error);
    alert('Erro ao processar pagamento PayPal');
  }
}
```

### 4. Páginas de Retorno

Criar `paypal-success.html`:
```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Pagamento PayPal - ONE WAY</title>
    <link rel="stylesheet" href="./Css/style.css">
</head>
<body>
    <div class="container">
        <h1>Processando seu pagamento...</h1>
        <div id="status"></div>
    </div>
    
    <script>
    // Capturar pagamento
    const urlParams = new URLSearchParams(window.location.search);
    const orderID = urlParams.get('token');
    
    fetch('/capture-paypal-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ orderID })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'COMPLETED') {
            document.getElementById('status').innerHTML = `
                <h2>✅ Pagamento aprovado!</h2>
                <p>Obrigado pela sua compra!</p>
                <a href="/" class="btn">Voltar ao site</a>
            `;
        } else {
            throw new Error('Pagamento não completado');
        }
    })
    .catch(error => {
        document.getElementById('status').innerHTML = `
            <h2>❌ Erro no pagamento</h2>
            <p>Entre em contato conosco.</p>
            <a href="/" class="btn">Voltar ao site</a>
        `;
    });
    </script>
</body>
</html>
```

### 5. Variáveis de Ambiente

Adicionar ao `.env`:
```env
# PayPal
PAYPAL_CLIENT_ID=seu_client_id_aqui
PAYPAL_CLIENT_SECRET=seu_secret_aqui
PAYPAL_SANDBOX=false
```

### 6. Atualizar Django Admin

Adicionar 'paypal' como opção em `FORMA_PAGAMENTO_CHOICES`:
```python
FORMA_PAGAMENTO_CHOICES = [
    ('pix', 'PIX'),
    ('2x', '2x sem juros'),
    ('4x', '4x com juros'),
    ('paypal', 'PayPal'),
]
```

## Recomendações

### ✅ Implementar PayPal SE:
1. Taxa de conversão do Mercado Pago estiver abaixo de 70%
2. Houver demanda significativa de clientes
3. Quiser atingir público internacional

### ❌ NÃO implementar PayPal SE:
1. Mercado Pago estiver funcionando bem
2. Público-alvo for exclusivamente brasileiro
3. Complexidade adicional não justificar ROI

## Alternativas Sugeridas

### Para melhorar taxa de aprovação:
1. **Stripe com PIX** - Já tem integração pronta, adicionar PIX
2. **PagSeguro** - Popular no Brasil, suporta PIX
3. **Cielo** - Tradicional, boa aprovação
4. **Asaas** - Simples, suporta PIX e boleto