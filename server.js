const express = require('express');
const cors = require('cors');
const path = require('path');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
const { MercadoPagoConfig, Preference } = require('mercadopago');
const axios = require('axios');
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
    
    // Aplicar desconto de 5% para PIX
    if (paymentMethod === 'pix') {
      amount = amount * 0.95; // 5% de desconto
    }

    const preferenceData = {
      items: [
        {
          title: `${productName} - Tamanho ${size}`,
          description: 'Camiseta ONE WAY 2025',
          picture_url: 'https://oneway-production.up.railway.app/img/camisetas/camiseta_marrom.jpeg',
          category_id: 'fashion',
          quantity: 1,
          currency_id: 'BRL',
          unit_price: amount
        }
      ],
      payment_methods: {
        excluded_payment_methods: [],
        excluded_payment_types: [
          { id: 'ticket' }       // Boletos em geral
        ],
        installments: 4, // Até 4 parcelas
        default_installments: 1
      },
      back_urls: {
        success: process.env.MP_SUCCESS_URL || 'https://oneway-production.up.railway.app/mp-success',
        failure: process.env.MP_CANCEL_URL || 'https://oneway-production.up.railway.app/mp-cancel',
        pending: process.env.MP_SUCCESS_URL || 'https://oneway-production.up.railway.app/mp-success'
      },
      auto_return: 'approved',
      external_reference: `${productName}_${size}_${Date.now()}`,
      metadata: {
        product_name: productName || '',
        size: size || '',
        price_id: priceId
      },
      statement_descriptor: 'ONE WAY 2025',
      expires: true,
      expiration_date_from: new Date().toISOString(),
      expiration_date_to: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 24h
    };

    // Enviar dados do pedido para o Django ANTES de criar a preferência MP
    let djangoPedidoId = null;
    if (process.env.DJANGO_API_URL && process.env.DJANGO_API_TOKEN) {
      try {
        const pedidoData = {
          // Dados do comprador (agora vindos do formulário)
          nome: req.body.nome || "Cliente Temporário",
          email: req.body.email || "cliente@temp.com", 
          telefone: req.body.telefone || "(00) 00000-0000",
          
          // Dados do pedido
          produto: productName.toLowerCase().replace(/ /g, '-'),
          tamanho: size,
          preco: amount,
          forma_pagamento: paymentMethod === 'pix' ? 'pix' : paymentMethod === '2x' ? '2x' : '4x',
          
          // Dados do Mercado Pago (serão atualizados depois)
          external_reference: preferenceData.external_reference
        };

        const djangoResponse = await axios.post(
          `${process.env.DJANGO_API_URL}/pedidos/`,
          pedidoData,
          {
            headers: {
              'Authorization': `Token ${process.env.DJANGO_API_TOKEN}`,
              'Content-Type': 'application/json'
            }
          }
        );

        djangoPedidoId = djangoResponse.data.id;
        console.log('Pedido criado no Django:', djangoPedidoId);
      } catch (error) {
        console.error('Erro ao enviar para Django:', error.response?.data || error.message);
        // Não bloquear o checkout se falhar o Django
      }
    }

    // Agora tentar criar a preferência do Mercado Pago
    const response = await preference.create({ body: preferenceData });

    // Se chegou até aqui, atualizar o pedido Django com o preference_id
    if (djangoPedidoId && process.env.DJANGO_API_URL && process.env.DJANGO_API_TOKEN) {
      try {
        await axios.post(
          `${process.env.DJANGO_API_URL}/pedidos/${djangoPedidoId}/atualizar_status/`,
          {
            preference_id: response.id
          },
          {
            headers: {
              'Authorization': `Token ${process.env.DJANGO_API_TOKEN}`,
              'Content-Type': 'application/json'
            }
          }
        );
        console.log('Preference ID atualizado no Django');
      } catch (error) {
        console.error('Erro ao atualizar preference_id:', error.response?.data || error.message);
      }
    }

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