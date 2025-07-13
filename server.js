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
const preference = new Preference(mercadoPagoClient);

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

// Páginas de checkout Stripe
app.get('/success', (req, res) => {
  res.sendFile(path.join(__dirname, 'success.html'));
});

app.get('/cancel', (req, res) => {
  res.sendFile(path.join(__dirname, 'cancel.html'));
});

// Páginas de checkout Mercado Pago
app.get('/mp-success', (req, res) => {
  res.sendFile(path.join(__dirname, 'mp-success.html'));
});

app.get('/mp-cancel', (req, res) => {
  res.sendFile(path.join(__dirname, 'mp-cancel.html'));
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

// Endpoint para criar preferência de pagamento Mercado Pago
app.post('/create-mp-checkout', async (req, res) => {
  try {
    const { priceId, productName, size, paymentMethod, installments } = req.body;

    if (!priceId) {
      return res.status(400).json({ 
        error: 'priceId é obrigatório' 
      });
    }

    // Valor base das camisetas
    let amount = 120.00;
    
    // Configurações específicas por método de pagamento
    let paymentConfig = {};
    let description = `${productName} - Tamanho ${size}`;
    
    if (paymentMethod === 'pix') {
      amount = amount * 0.95; // 5% de desconto para PIX
      description += ' (PIX - 5% desconto)';
      paymentConfig = {
        excluded_payment_methods: [],
        excluded_payment_types: [
          { id: 'credit_card' },    // Bloquear cartão de crédito
          { id: 'debit_card' },     // Bloquear cartão de débito
          { id: 'ticket' },         // Bloquear boletos
          { id: 'bank_transfer' },  // Bloquear transferência
          { id: 'atm' },           // Bloquear caixa eletrônico
          { id: 'digital_currency' } // Bloquear moedas digitais
        ],
        installments: 1,
        default_installments: 1
      };
    } else {
      // Cartão (sem desconto)
      paymentConfig = {
        excluded_payment_methods: [],
        excluded_payment_types: [
          { id: 'ticket' }         // Bloquear apenas boletos
        ],
        installments: paymentMethod === '2x' ? 2 : 4,
        default_installments: paymentMethod === '2x' ? 2 : 1
      };
    }

    const preferenceData = {
      items: [
        {
          title: description,
          description: 'Camiseta ONE WAY 2025',
          picture_url: 'https://oneway-production.up.railway.app/img/camisetas/camiseta_marrom.jpeg',
          category_id: 'fashion',
          quantity: 1,
          currency_id: 'BRL',
          unit_price: amount
        }
      ],
      payment_methods: paymentConfig,
      payer: {},
      back_urls: {
        success: process.env.MP_SUCCESS_URL || 'https://oneway-production.up.railway.app/mp-success',
        failure: process.env.MP_CANCEL_URL || 'https://oneway-production.up.railway.app/mp-cancel',
        pending: process.env.MP_SUCCESS_URL || 'https://oneway-production.up.railway.app/mp-success'
      },
      auto_return: 'approved',
      purpose: 'wallet_purchase',
      binary_mode: false,
      external_reference: `${productName}_${size}_${paymentMethod}_${Date.now()}`,
      metadata: {
        product_name: productName || '',
        size: size || '',
        price_id: priceId,
        payment_method: paymentMethod,
        original_amount: 120.00,
        final_amount: amount
      },
      statement_descriptor: 'ONE WAY 2025',
      expires: true,
      expiration_date_from: new Date().toISOString(),
      expiration_date_to: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 24h
      additional_info: `Produto: ${productName} | Tamanho: ${size} | Pagamento: ${paymentMethod}`
    };

    const response = await preference.create({ body: preferenceData });

    res.json({ 
      checkout_url: response.init_point,
      preference_id: response.id 
    });
  } catch (error) {
    console.error('Erro ao criar preferência MP:', error);
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