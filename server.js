const express = require('express');
const cors = require('cors');
const path = require('path');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('.'));

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'OK',
    timestamp: new Date().toISOString(),
    service: 'ONE WAY Backend',
    version: '1.0.0'
  });
});

// Servir arquivos estáticos (site)
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Endpoint para criar sessão de checkout Stripe
app.post('/create-checkout-session', async (req, res) => {
  try {
    const { priceId, productName, size } = req.body;

    if (!priceId) {
      return res.status(400).json({ 
        error: 'priceId é obrigatório' 
      });
    }

    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [
        {
          price: priceId,
          quantity: 1,
        },
      ],
      mode: 'payment',
      success_url: process.env.SUCCESS_URL,
      cancel_url: process.env.CANCEL_URL,
      metadata: {
        product_name: productName || '',
        size: size || ''
      }
    });

    res.json({ url: session.url });
  } catch (error) {
    console.error('Erro ao criar sessão Stripe:', error);
    res.status(500).json({ 
      error: 'Erro interno do servidor',
      message: error.message 
    });
  }
});

// Endpoint para listar produtos e preços do Stripe
app.get('/stripe-products', async (req, res) => {
  try {
    console.log('Listando produtos Stripe...');
    const products = await stripe.products.list({ limit: 100 });
    console.log(`Encontrados ${products.data.length} produtos`);
    
    const productData = [];

    for (const product of products.data) {
      console.log(`Produto: ${product.id} - ${product.name}`);
      const prices = await stripe.prices.list({ 
        product: product.id,
        limit: 100 
      });
      console.log(`  Preços encontrados: ${prices.data.length}`);
      
      productData.push({
        product_id: product.id,
        name: product.name,
        prices: prices.data.map(price => ({
          price_id: price.id,
          amount: price.unit_amount / 100,
          currency: price.currency
        }))
      });
    }

    res.json({ 
      products: productData,
      debug: {
        stripe_key_prefix: process.env.STRIPE_SECRET_KEY?.substring(0, 8) + '...',
        total_products: products.data.length
      }
    });
  } catch (error) {
    console.error('Erro ao listar produtos Stripe:', error);
    res.status(500).json({ error: error.message });
  }
});

// Rota para testar variáveis de ambiente
app.get('/env-check', (req, res) => {
  res.json({
    stripe_configured: !!process.env.STRIPE_SECRET_KEY,
    node_env: process.env.NODE_ENV || 'development'
  });
});

// Iniciar servidor
app.listen(PORT, () => {
  console.log(`🚀 Servidor rodando na porta ${PORT}`);
  console.log(`📍 Health check: http://localhost:${PORT}/health`);
  console.log(`🌐 Site: http://localhost:${PORT}`);
  
  // Verificar configuração Stripe
  if (!process.env.STRIPE_SECRET_KEY) {
    console.log('⚠️  STRIPE_SECRET_KEY não configurada');
  } else {
    console.log('✅ STRIPE_SECRET_KEY configurada');
  }
});

module.exports = app;