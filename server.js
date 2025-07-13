const express = require('express');
const cors = require('cors');
const path = require('path');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
const { MercadoPagoConfig, Preference } = require('mercadopago');
require('dotenv').config();

// Configurar Mercado Pago
const mercadoPagoClient = new MercadoPagoConfig({ 
  accessToken: process.env.MERCADOPAGO_ACCESS_TOKEN 
});

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

// Páginas de checkout
app.get('/success', (req, res) => {
  res.sendFile(path.join(__dirname, 'success.html'));
});

app.get('/cancel', (req, res) => {
  res.sendFile(path.join(__dirname, 'cancel.html'));
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


// Health check específico Mercado Pago
app.get('/mp-health', (req, res) => {
  const mpConfigured = !!process.env.MERCADOPAGO_ACCESS_TOKEN;
  const tokenType = process.env.MERCADOPAGO_ACCESS_TOKEN?.startsWith('TEST-') ? 'teste' : 
                   process.env.MERCADOPAGO_ACCESS_TOKEN?.startsWith('APP_USR') ? 'produção' : 'inválido';
  
  res.json({
    status: mpConfigured ? 'OK' : 'ERROR',
    mercadopago_configured: mpConfigured,
    token_type: tokenType,
    timestamp: new Date().toISOString(),
    service: 'Mercado Pago Integration'
  });
});

// Rota para testar variáveis de ambiente
app.get('/env-check', (req, res) => {
  res.json({
    stripe_configured: !!process.env.STRIPE_SECRET_KEY,
    mercadopago_configured: !!process.env.MERCADOPAGO_ACCESS_TOKEN,
    node_env: process.env.NODE_ENV || 'development'
  });
});

// Iniciar servidor
app.listen(PORT, () => {
  console.log(`🚀 Servidor rodando na porta ${PORT}`);
  console.log(`📍 Health check: http://localhost:${PORT}/health`);
  console.log(`📍 MP Health check: http://localhost:${PORT}/mp-health`);
  console.log(`🌐 Site: http://localhost:${PORT}`);
  
  // Verificar configuração Stripe
  if (!process.env.STRIPE_SECRET_KEY) {
    console.log('⚠️  STRIPE_SECRET_KEY não configurada');
  } else {
    console.log('✅ STRIPE_SECRET_KEY configurada');
  }
  
  // Verificar configuração Mercado Pago
  if (!process.env.MERCADOPAGO_ACCESS_TOKEN) {
    console.log('⚠️  MERCADOPAGO_ACCESS_TOKEN não configurada');
  } else {
    const tokenType = process.env.MERCADOPAGO_ACCESS_TOKEN.startsWith('TEST-') ? 'TESTE' : 'PRODUÇÃO';
    console.log(`✅ MERCADOPAGO_ACCESS_TOKEN configurada (${tokenType})`);
  }
});

module.exports = app;