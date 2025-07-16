const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
const { MercadoPagoConfig, Preference } = require('mercadopago');
const axios = require('axios');
require('dotenv').config();

// Cache do catálogo de produtos para performance e segurança
let productsCache = null;
let productsCacheTime = 0;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutos

function getProductsCatalog() {
  const now = Date.now();
  
  // Usar cache se ainda válido
  if (productsCache && (now - productsCacheTime) < CACHE_DURATION) {
    return productsCache;
  }
  
  try {
    const productsPath = path.join(__dirname, 'products.json');
    const data = fs.readFileSync(productsPath, 'utf8');
    productsCache = JSON.parse(data);
    productsCacheTime = now;
    return productsCache;
  } catch (error) {
    console.error('Erro crítico ao carregar products.json:', error);
    throw new Error('Catálogo de produtos indisponível');
  }
}

// Configurações da API Django
const DJANGO_API_URL = process.env.DJANGO_API_URL || 'http://localhost:8000/api';
const DJANGO_API_TOKEN = process.env.DJANGO_API_TOKEN;

// Configurar Mercado Pago
const mercadoPagoClient = new MercadoPagoConfig({ 
  accessToken: process.env.MERCADOPAGO_ACCESS_TOKEN 
});
const preference = new Preference(mercadoPagoClient);

// Configurar PayPal
const https = require('https');
const PAYPAL_CLIENT_ID = process.env.PAYPAL_CLIENT_ID;
const PAYPAL_CLIENT_SECRET = process.env.PAYPAL_CLIENT_SECRET;
const PAYPAL_BASE_URL = process.env.PAYPAL_ENVIRONMENT === 'sandbox' 
  ? 'https://api.sandbox.paypal.com' 
  : 'https://api.paypal.com';

// Função para obter token PayPal
async function getPayPalAccessToken() {
  const auth = Buffer.from(`${PAYPAL_CLIENT_ID}:${PAYPAL_CLIENT_SECRET}`).toString('base64');
  
  return new Promise((resolve, reject) => {
    const options = {
      hostname: PAYPAL_BASE_URL.replace('https://', ''),
      port: 443,
      path: '/v1/oauth2/token',
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Accept-Language': 'en_US',
        'Authorization': `Basic ${auth}`,
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    };
    
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) {
          const tokenData = JSON.parse(data);
          resolve(tokenData.access_token);
        } else {
          reject(new Error(`PayPal auth failed: ${res.statusCode}`));
        }
      });
    });
    
    req.on('error', reject);
    req.write('grant_type=client_credentials');
    req.end();
  });
}

// Função para fazer request HTTP PayPal
function makePayPalRequest(options, postData = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body: data
        });
      });
    });
    
    req.on('error', reject);
    if (postData) req.write(postData);
    req.end();
  });
}

const app = express();
const PORT = process.env.PORT || 3000;

// Função para mapear nome do produto para ID do Django
function mapearProdutoParaId(productName) {
  const mapping = {
    'Camiseta One Way Marrom': 'camiseta-marrom',
    'Camiseta Jesus': 'camiseta-jesus',
    'Camiseta ONE WAY Off White': 'camiseta-oneway-branca',
    'Camiseta The Way': 'camiseta-the-way'
  };
  
  const produtoMapeado = mapping[productName];
  
  if (!produtoMapeado) {
    console.error(`❌ ERRO: Produto não encontrado no mapeamento: "${productName}"`);
    console.error('Produtos válidos:', Object.keys(mapping));
    // Lançar erro em vez de retornar valor padrão incorreto
    throw new Error(`Produto não encontrado: ${productName}`);
  }
  
  console.log(`✅ Produto mapeado: "${productName}" -> "${produtoMapeado}"`);
  return produtoMapeado;
}

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

// Proxy para Django Admin
app.use('/admin', (req, res) => {
  const url = `http://localhost:8000${req.originalUrl}`;
  setTimeout(() => {
    axios.get(url).then(response => {
      res.send(response.data);
    }).catch(error => {
      console.error('Erro proxy Django:', error.message);
      res.status(500).send('Django ainda não disponível, aguarde...');
    });
  }, 1000);
});

// Proxy para Django API  
app.use('/django-api', (req, res) => {
  const url = `http://localhost:8000/api${req.url}`;
  axios.get(url).then(response => {
    res.json(response.data);
  }).catch(error => {
    res.status(500).json({error: 'Django API não disponível'});
  });
});

// Servir arquivos estáticos (site)
app.get('/', (req, res) => {
  console.log('📍 Acessando rota raiz /');
  console.log('📁 Diretório atual:', __dirname);
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

// Páginas de checkout PayPal
app.get('/paypal-success', (req, res) => {
  res.sendFile(path.join(__dirname, 'paypal-success.html'));
});

app.get('/paypal-cancel', (req, res) => {
  res.sendFile(path.join(__dirname, 'paypal-cancel.html'));
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
    const { productId, priceId, productName, size, paymentMethod, installments, nome, email, telefone } = req.body;

    if (!priceId) {
      return res.status(400).json({ 
        error: 'priceId é obrigatório' 
      });
    }

    // SEGURANÇA: Buscar preço real do catálogo no servidor (ignora frontend)
    let productsData;
    try {
      productsData = getProductsCatalog();
    } catch (error) {
      return res.status(500).json({ 
        error: 'Serviço temporariamente indisponível. Tente novamente.' 
      });
    }

    // Encontrar produto pelo nome exato
    const product = Object.values(productsData.products)
      .find(p => p.title === productName);
    
    if (!product) {
      console.warn(`Produto não encontrado: "${productName}"`);
      return res.status(400).json({ 
        error: 'Produto não encontrado. Atualize a página e tente novamente.' 
      });
    }

    // FONTE ÚNICA DA VERDADE: preço sempre do servidor
    let amount = parseFloat(product.price);
    
    if (isNaN(amount) || amount <= 0) {
      console.error(`Preço inválido: ${productName} = ${product.price}`);
      return res.status(500).json({ 
        error: 'Configuração inválida do produto. Contate o suporte.' 
      });
    }
    
    // Aplicar desconto de 5% para PIX baseado no preço real
    const originalAmount = amount;
    if (paymentMethod === 'pix') {
      amount = amount * 0.95; // 5% de desconto
    }
    
    // Log de segurança: registrar preço usado vs enviado pelo frontend
    const frontendPrice = parseFloat(req.body.price);
    if (frontendPrice && Math.abs(frontendPrice - originalAmount) > 0.01) {
      console.warn(`🚨 TENTATIVA DE MANIPULAÇÃO DE PREÇO:
        Produto: ${productName}
        Preço real: R$ ${originalAmount.toFixed(2)}
        Preço enviado: R$ ${frontendPrice.toFixed(2)}
        IP: ${req.ip}
        User-Agent: ${req.get('User-Agent')}`);
    }
    
    console.log(`✅ Checkout seguro: ${productName} - ${paymentMethod} - R$ ${amount.toFixed(2)}`);
    console.log(`🔍 Debug - ProductId: ${productId}, Product: ${product.id}`);
    console.log(`🖼️ Imagem do produto: ${product.image}`);

    // NOVO FLUXO: Criar pedido ANTES da preferência MP
    console.log('💾 ETAPA 1: Criando pedido pendente no Django...');
    
    // Gerar external_reference único sem espaços
    let produtoIdRef;
    try {
      produtoIdRef = mapearProdutoParaId(productName).replace('camiseta-', '').replace('-', '').toUpperCase();
    } catch (error) {
      // Se falhar no mapeamento, usar o productId numérico
      produtoIdRef = productId || 'UNKNOWN';
    }
    const externalReference = `ONEWAY-${produtoIdRef}-${size}-${Date.now()}`;
    
    // Preparar dados do pedido
    const pedidoData = {
      // Dados do comprador
      nome: nome || '',
      email: email || '',
      telefone: telefone || '',
      
      // Dados do produto
      produto: productId ? (() => {
        // Mapear ID numérico para string do Django
        const idMapping = {
          '1': 'camiseta-marrom',
          '2': 'camiseta-jesus',
          '3': 'camiseta-oneway-branca',
          '4': 'camiseta-the-way'
        };
        
        const produtoMapeado = idMapping[productId];
        if (!produtoMapeado) {
          console.error(`❌ ProductId inválido: ${productId}`);
          throw new Error(`ProductId inválido: ${productId}`);
        }
        return produtoMapeado;
      })() : (() => {
        // Fallback: tentar mapear pelo nome
        try {
          return mapearProdutoParaId(productName);
        } catch (error) {
          console.error('❌ Falha no mapeamento do produto:', error.message);
          throw new Error('Produto inválido - verifique os dados enviados');
        }
      })(),
      tamanho: size,
      preco: amount,
      forma_pagamento: paymentMethod === 'pix' ? 'pix' : paymentMethod === '2x' ? '2x' : '4x',
      
      // Status inicial
      status_pagamento: 'pending',
      external_reference: externalReference
    };
    
    console.log('📤 Dados do pedido:', pedidoData);
    
    // Criar pedido no Django
    let pedidoCriado;
    try {
      if (!DJANGO_API_TOKEN) {
        throw new Error('Token Django não configurado');
      }
      
      const pedidoResponse = await axios.post(
        `${DJANGO_API_URL}/pedidos/`,
        pedidoData,
        {
          headers: {
            'Authorization': `Token ${DJANGO_API_TOKEN}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      pedidoCriado = pedidoResponse.data;
      console.log('✅ Pedido criado:', pedidoCriado.id);
      
    } catch (error) {
      console.error('❌ Erro ao criar pedido Django:', error.response?.data || error.message);
      return res.status(500).json({
        error: 'Erro ao processar pedido. Tente novamente.',
        details: error.response?.data || error.message
      });
    }

    // ETAPA 2: Criar preferência MP com external_reference
    console.log('🏪 ETAPA 2: Criando preferência Mercado Pago...');
    
    const preferenceData = {
      items: [
        {
          title: `${productName} - Tamanho ${size}`,
          description: 'Camiseta ONE WAY 2025',
          picture_url: product.image ? `https://oneway.mevamfranca.com.br${product.image.replace('./', '/')}` : 'https://oneway.mevamfranca.com.br/img/camisetas/camiseta_marrom.jpeg',
          category_id: 'fashion',
          quantity: 1,
          currency_id: 'BRL',
          unit_price: amount
        }
      ],
      payment_methods: (() => {
        // Configuração base
        let payment_methods = {
          excluded_payment_methods: [],
          excluded_payment_types: [
            { id: 'ticket' }  // Boletos sempre excluídos
          ],
          installments: 4,
          default_installments: 1
        };

        // Configuração dinâmica baseada na escolha do usuário
        console.log(`🔧 Configurando métodos de pagamento para: ${paymentMethod}`);
        
        if (paymentMethod === 'pix') {
          // Quando PIX: excluir cartões
          payment_methods.excluded_payment_types.push(
            { id: 'credit_card' },
            { id: 'debit_card' }
          );
          payment_methods.installments = 1;
          console.log('✅ PIX: Cartões excluídos');
        } else if (paymentMethod === '2x') {
          // Quando 2x: limitar parcelamento e excluir PIX
          payment_methods.excluded_payment_types.push(
            { id: 'bank_transfer' }  // PIX
          );
          payment_methods.installments = 2;
          payment_methods.default_installments = 2;
          console.log('✅ 2x: PIX excluído, máximo 2 parcelas');
        } else if (paymentMethod === '4x') {
          // Quando 4x: permitir até 4 parcelas e excluir PIX
          payment_methods.excluded_payment_types.push(
            { id: 'bank_transfer' }  // PIX
          );
          payment_methods.installments = 4;
          payment_methods.default_installments = 1;
          console.log('✅ 4x: PIX excluído, máximo 4 parcelas');
        } else {
          console.log(`⚠️ Método de pagamento não reconhecido: ${paymentMethod}`);
        }
        
        console.log('🔧 Configuração final payment_methods:', JSON.stringify(payment_methods, null, 2));

        return payment_methods;
      })(),
      back_urls: {
        success: `${process.env.MP_SUCCESS_URL || 'https://oneway.mevamfranca.com.br/mp-success'}?external_reference=${externalReference}`,
        failure: process.env.MP_CANCEL_URL || 'https://oneway.mevamfranca.com.br/mp-cancel',
        pending: `${process.env.MP_SUCCESS_URL || 'https://oneway.mevamfranca.com.br/mp-success'}?external_reference=${externalReference}`
      },
      auto_return: 'approved',
      external_reference: externalReference,
      metadata: {
        // Dados do comprador
        comprador_nome: nome || '',
        comprador_email: email || '',
        comprador_telefone: telefone || '',
        // Dados do produto
        product_id: productId || '',
        product_name: productName || '',
        size: size || '',
        price_id: priceId,
        // Dados do pedido
        forma_pagamento: paymentMethod === 'pix' ? 'pix' : paymentMethod === '2x' ? '2x' : '4x',
        preco_original: amount,
        // ID do pedido Django para referência
        django_pedido_id: pedidoCriado.id
      },
      statement_descriptor: 'ONE WAY 2025',
      expires: true,
      expiration_date_from: new Date().toISOString(),
      expiration_date_to: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 24h
    };

    // Criar preferência no Mercado Pago
    let mpResponse;
    try {
      mpResponse = await preference.create({ body: preferenceData });
      console.log('✅ Preferência MP criada:', mpResponse.id);
      
    } catch (error) {
      console.error('❌ Erro ao criar preferência MP:', error);
      
      // Se falhar na criação da preferência, marcar pedido como erro
      try {
        await axios.post(
          `${DJANGO_API_URL}/pedidos/${pedidoCriado.id}/atualizar_status/`,
          {
            status_pagamento: 'erro_mp',
            observacoes: 'Erro ao criar preferência no Mercado Pago'
          },
          {
            headers: {
              'Authorization': `Token ${DJANGO_API_TOKEN}`,
              'Content-Type': 'application/json'
            }
          }
        );
      } catch (updateError) {
        console.error('❌ Erro ao atualizar status do pedido:', updateError);
      }
      
      return res.status(500).json({
        error: 'Erro ao configurar pagamento. Tente novamente.',
        details: error.message
      });
    }

    // ETAPA 3: Atualizar pedido com preference_id
    console.log('🔄 ETAPA 3: Atualizando pedido com preference_id...');
    
    try {
      await axios.post(
        `${DJANGO_API_URL}/pedidos/${pedidoCriado.id}/atualizar_status/`,
        {
          preference_id: mpResponse.id,
          observacoes: 'Preferência MP criada com sucesso'
        },
        {
          headers: {
            'Authorization': `Token ${DJANGO_API_TOKEN}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      console.log('✅ Pedido atualizado com preference_id');
      
    } catch (error) {
      console.error('⚠️ Erro ao atualizar pedido (não crítico):', error);
      // Não bloquear o fluxo se apenas a atualização falhar
    }
    
    console.log('🚀 FLUXO COMPLETO: Pedido criado e preferência MP configurada');

    res.json({ 
      checkout_url: mpResponse.init_point,
      preference_id: mpResponse.id,
      pedido_id: pedidoCriado.id,
      external_reference: externalReference
    });
  } catch (error) {
    console.error('Erro ao criar preferência MP:', error);
    res.status(500).json({ 
      error: 'Erro interno do servidor',
      message: error.message 
    });
  }
});

// Endpoint para buscar detalhes do pagamento MP (usado pela página de sucesso)
app.get('/api/mp-payment-details/:paymentId', async (req, res) => {
  try {
    const { paymentId } = req.params;
    
    if (!paymentId) {
      return res.status(400).json({ error: 'Payment ID é obrigatório' });
    }
    
    console.log(`🔍 Buscando detalhes do pagamento MP: ${paymentId}`);
    
    // Buscar detalhes do pagamento no MP
    const { Payment } = require('mercadopago');
    const payment = new Payment(mercadoPagoClient);
    
    const paymentData = await payment.get({ id: paymentId });
    
    if (!paymentData) {
      return res.status(404).json({ error: 'Pagamento não encontrado' });
    }
    
    // Buscar metadata da preferência
    let metadata = {};
    
    // Primeiro tentar pegar preference_id dos parâmetros da URL (mais confiável)
    const urlParams = req.query;
    let preferenceId = urlParams.preference_id;
    
    // Se não veio na URL, tentar pegar do paymentData
    if (!preferenceId) {
      preferenceId = paymentData.additional_info?.preference_id;
    }
    
    if (preferenceId) {
      try {
        console.log(`🔍 Buscando preferência: ${preferenceId}`);
        const preferenceData = await preference.get({ preferenceId });
        metadata = preferenceData.metadata || {};
        console.log(`📋 Metadata da preferência:`, metadata);
      } catch (prefError) {
        console.warn('⚠️ Erro ao buscar preferência:', prefError.message);
        // Tentar buscar metadata do próprio payment como fallback
        metadata = paymentData.metadata || {};
      }
    } else {
      console.warn('⚠️ Preference ID não encontrado');
    }
    
    console.log(`✅ Metadata encontrada:`, metadata);
    
    res.json({
      payment_status: paymentData.status,
      payment_id: paymentData.id,
      external_reference: paymentData.external_reference,
      metadata: metadata
    });
    
  } catch (error) {
    console.error('Erro ao buscar detalhes MP:', error);
    res.status(500).json({ 
      error: 'Erro ao consultar Mercado Pago',
      details: error.message 
    });
  }
});

// Endpoint proxy para buscar pedido por external_reference
app.get('/api/django/pedidos/referencia/:external_reference/', async (req, res) => {
  try {
    const { external_reference } = req.params;
    
    if (!DJANGO_API_TOKEN) {
      return res.status(500).json({ 
        error: 'Configuração Django incompleta' 
      });
    }
    
    console.log('🔍 Buscando pedido por external_reference:', external_reference);
    
    const response = await axios.get(
      `${DJANGO_API_URL}/pedidos/referencia/${encodeURIComponent(external_reference)}/`,
      {
        headers: {
          'Authorization': `Token ${DJANGO_API_TOKEN}`,
          'Accept': 'application/json'
        }
      }
    );
    
    console.log('✅ Pedido encontrado:', response.data.id);
    res.json(response.data);
    
  } catch (error) {
    console.error('❌ Erro ao buscar pedido:', error.response?.data || error.message);
    
    if (error.response?.status === 404) {
      res.status(404).json({ 
        error: 'Pedido não encontrado',
        external_reference: req.params.external_reference
      });
    } else {
      res.status(500).json({ 
        error: 'Erro interno ao buscar pedido',
        details: error.message
      });
    }
  }
});

// Endpoint proxy para atualizar status do pedido
app.post('/api/django/pedidos/:id/atualizar_status/', async (req, res) => {
  try {
    const { id } = req.params;
    
    if (!DJANGO_API_TOKEN) {
      return res.status(500).json({ 
        error: 'Configuração Django incompleta' 
      });
    }
    
    console.log('🔄 Atualizando status do pedido:', id);
    console.log('📤 Dados para atualização:', req.body);
    
    const response = await axios.post(
      `${DJANGO_API_URL}/pedidos/${id}/atualizar_status/`,
      req.body,
      {
        headers: {
          'Authorization': `Token ${DJANGO_API_TOKEN}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    console.log('✅ Status atualizado com sucesso:', response.data.id);
    res.json(response.data);
    
  } catch (error) {
    console.error('❌ Erro ao atualizar status:', error.response?.data || error.message);
    
    if (error.response?.status === 404) {
      res.status(404).json({ 
        error: 'Pedido não encontrado para atualização',
        pedido_id: req.params.id
      });
    } else if (error.response?.status === 400) {
      res.status(400).json(error.response.data);
    } else {
      res.status(500).json({ 
        error: 'Erro interno ao atualizar pedido',
        details: error.message
      });
    }
  }
});

// Endpoint proxy para Django API (criar pedidos)
app.post('/api/django/pedidos/', async (req, res) => {
  try {
    if (!DJANGO_API_TOKEN) {
      return res.status(500).json({ 
        error: 'Configuração Django incompleta' 
      });
    }
    
    console.log('🔗 Enviando pedido para Django API...');
    
    const response = await axios.post(
      `${DJANGO_API_URL}/pedidos/`,
      req.body,
      {
        headers: {
          'Authorization': `Token ${DJANGO_API_TOKEN}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    console.log('✅ Pedido criado no Django:', response.data.id);
    res.json(response.data);
    
  } catch (error) {
    console.error('❌ Erro no proxy Django:', error.response?.data || error.message);
    
    if (error.response?.status === 400) {
      // Erro de validação do Django
      res.status(400).json(error.response.data);
    } else {
      res.status(500).json({ 
        error: 'Erro interno ao processar pedido',
        details: error.message
      });
    }
  }
});

// Endpoint para criar ordem PayPal
app.post('/create-paypal-order', async (req, res) => {
  try {
    const { productName, size, nome, email, telefone } = req.body;
    
    console.log('🅿️ Criando ordem PayPal para cartão...');
    console.log('📦 Produto:', productName, 'Tamanho:', size);
    console.log('👤 Cliente:', nome, email, telefone);
    console.log('🔧 DEBUG: PayPal Environment:', process.env.PAYPAL_ENVIRONMENT);
    console.log('🔧 DEBUG: PayPal Base URL:', PAYPAL_BASE_URL);
    console.log('🔧 DEBUG: Client ID exists:', !!PAYPAL_CLIENT_ID);
    console.log('🔧 DEBUG: Client Secret exists:', !!PAYPAL_CLIENT_SECRET);
    
    // Validar dados obrigatórios
    if (!productName || !size || !nome || !email || !telefone) {
      console.error('❌ DEBUG: Dados obrigatórios faltando');
      return res.status(400).json({
        error: 'Dados obrigatórios: productName, size, nome, email, telefone'
      });
    }
    
    // Validar credenciais PayPal
    if (!PAYPAL_CLIENT_ID || !PAYPAL_CLIENT_SECRET) {
      console.error('❌ DEBUG: Credenciais PayPal não configuradas');
      return res.status(500).json({
        error: 'Credenciais PayPal não configuradas'
      });
    }
    
    console.log('✅ DEBUG: Validações iniciais passaram');
    
    // SEGURANÇA: Buscar preço real do catálogo no servidor
    console.log('📋 DEBUG: Carregando catálogo de produtos...');
    let productsData;
    try {
      productsData = getProductsCatalog();
      console.log('✅ DEBUG: Catálogo carregado com sucesso');
    } catch (error) {
      console.error('❌ DEBUG: Erro ao carregar catálogo:', error.message);
      return res.status(500).json({ 
        error: 'Serviço temporariamente indisponível. Tente novamente.' 
      });
    }

    // Encontrar produto pelo nome exato
    const product = Object.values(productsData.products)
      .find(p => p.title === productName);
    
    if (!product) {
      console.warn(`Produto não encontrado: "${productName}"`);
      return res.status(400).json({ 
        error: 'Produto não encontrado. Atualize a página e tente novamente.' 
      });
    }

    // FONTE ÚNICA DA VERDADE: preço sempre do servidor
    const amount = parseFloat(product.price);
    
    if (isNaN(amount) || amount <= 0) {
      console.error(`Preço inválido: ${productName} = ${product.price}`);
      return res.status(500).json({ 
        error: 'Configuração inválida do produto. Contate o suporte.' 
      });
    }
    
    console.log(`✅ Preço validado: R$ ${amount.toFixed(2)}`);
    
    // ETAPA 1: Criar pedido pendente no Django
    console.log('💾 ETAPA 1: Criando pedido pendente no Django...');
    
    const externalReference = `PAYPAL-${Date.now()}`;
    
    const pedidoData = {
      nome,
      email,
      telefone,
      produto: mapearProdutoParaId(productName),
      tamanho: size,
      preco: amount,
      forma_pagamento: 'paypal',
      status_pagamento: 'pending',
      external_reference: externalReference,
      observacoes: 'Pedido PayPal - aguardando pagamento'
    };
    
    console.log('📤 Dados do pedido:', pedidoData);
    
    let pedidoCriado;
    try {
      const pedidoResponse = await axios.post(
        `${DJANGO_API_URL}/pedidos/`,
        pedidoData,
        {
          headers: {
            'Authorization': `Token ${DJANGO_API_TOKEN}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      pedidoCriado = pedidoResponse.data;
      console.log('✅ Pedido criado no Django:', pedidoCriado.id);
      
    } catch (error) {
      console.error('❌ Erro ao criar pedido Django:', error.response?.data || error.message);
      return res.status(500).json({
        error: 'Erro ao processar pedido. Tente novamente.',
        details: error.response?.data || error.message
      });
    }
    
    // ETAPA 2: Obter token PayPal
    console.log('🔑 ETAPA 2: Obtendo token PayPal...');
    
    let accessToken;
    try {
      accessToken = await getPayPalAccessToken();
      console.log('✅ DEBUG: Token PayPal obtido com sucesso');
    } catch (error) {
      console.error('❌ DEBUG: Erro ao obter token PayPal:', error.message);
      console.error('❌ DEBUG: Stack trace:', error.stack);
      return res.status(500).json({
        error: 'Erro de autenticação PayPal. Tente novamente.',
        details: error.message
      });
    }
    
    // ETAPA 3: Criar ordem no PayPal
    console.log('🏪 ETAPA 3: Criando ordem PayPal...');
    
    const orderData = {
      intent: 'CAPTURE',
      purchase_units: [
        {
          amount: {
            currency_code: 'BRL',
            value: amount.toFixed(2)
          },
          description: `${productName} - Tamanho ${size}`,
          custom_id: externalReference
        }
      ],
      application_context: {
        brand_name: 'ONE WAY 2025',
        locale: 'pt-BR',
        landing_page: 'GUEST_CHECKOUT', // Força guest checkout sem conta
        shipping_preference: 'NO_SHIPPING',
        user_action: 'PAY_NOW',
        return_url: `${process.env.BASE_URL || 'https://oneway.mevamfranca.com.br'}/paypal-success?external_reference=${externalReference}&pedido_id=${pedidoCriado.id}`,
        cancel_url: `${process.env.BASE_URL || 'https://oneway.mevamfranca.com.br'}/paypal-cancel`
      },
      payment_method: {
        payee_preferred: 'IMMEDIATE_PAYMENT_REQUIRED' // Pagamento imediato sem conta
      }
    };
    
    console.log('📤 DEBUG: Dados da ordem PayPal:', JSON.stringify(orderData, null, 2));
    
    const orderOptions = {
      hostname: PAYPAL_BASE_URL.replace('https://', ''),
      port: 443,
      path: '/v2/checkout/orders',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
        'Accept': 'application/json',
        'Prefer': 'return=representation'
      }
    };
    
    try {
      console.log('🔄 DEBUG: Fazendo requisição para PayPal...');
      const orderResponse = await makePayPalRequest(orderOptions, JSON.stringify(orderData));
      
      console.log('📥 DEBUG: Resposta PayPal - Status:', orderResponse.statusCode);
      console.log('📥 DEBUG: Resposta PayPal - Body:', orderResponse.body);
      
      if (orderResponse.statusCode === 201) {
        const orderResult = JSON.parse(orderResponse.body);
        console.log('✅ DEBUG: Ordem PayPal criada com sucesso:', orderResult.id);
        
        // ETAPA 4: Atualizar pedido com order ID
        console.log('🔄 ETAPA 4: Atualizando pedido com order ID...');
        
        try {
          await axios.post(
            `${DJANGO_API_URL}/pedidos/${pedidoCriado.id}/atualizar_status/`,
            {
              preference_id: orderResult.id,
              observacoes: 'Ordem PayPal criada - aguardando pagamento'
            },
            {
              headers: {
                'Authorization': `Token ${DJANGO_API_TOKEN}`,
                'Content-Type': 'application/json'
              }
            }
          );
          
          console.log('✅ Pedido atualizado com order ID');
          
        } catch (updateError) {
          console.error('⚠️ Erro ao atualizar pedido (não crítico):', updateError.message);
        }
        
        // Encontrar link de aprovação
        const approveLink = orderResult.links?.find(link => link.rel === 'approve');
        
        if (approveLink) {
          console.log('🚀 FLUXO COMPLETO: Pedido criado e ordem PayPal configurada');
          
          res.json({
            success: true,
            order_id: orderResult.id,
            approval_url: approveLink.href,
            pedido_id: pedidoCriado.id,
            external_reference: externalReference
          });
        } else {
          throw new Error('Link de aprovação não encontrado');
        }
        
      } else {
        console.error('❌ DEBUG: Erro ao criar ordem PayPal - Status:', orderResponse.statusCode);
        console.error('❌ DEBUG: Erro ao criar ordem PayPal - Body:', orderResponse.body);
        return res.status(500).json({
          error: 'Erro ao criar ordem PayPal',
          details: orderResponse.body
        });
      }
      
    } catch (error) {
      console.error('❌ DEBUG: Erro na comunicação com PayPal:', error.message);
      console.error('❌ DEBUG: Stack trace:', error.stack);
      return res.status(500).json({
        error: 'Erro ao processar pagamento PayPal',
        details: error.message
      });
    }
    
  } catch (error) {
    console.error('❌ DEBUG: Erro geral no create-paypal-order:', error.message);
    console.error('❌ DEBUG: Stack trace:', error.stack);
    res.status(500).json({
      error: 'Erro interno do servidor',
      message: error.message,
      stack: error.stack
    });
  }
});

// Endpoint para capturar pagamento PayPal
app.post('/capture-paypal-order', async (req, res) => {
  try {
    const { orderID, external_reference, pedido_id } = req.body;
    
    console.log('🅿️ Capturando pagamento PayPal...');
    console.log('📦 Order ID:', orderID);
    console.log('🔗 External Reference:', external_reference);
    console.log('🆔 Pedido ID:', pedido_id);
    
    // Validar dados obrigatórios
    if (!orderID) {
      return res.status(400).json({
        error: 'Order ID é obrigatório'
      });
    }
    
    // Validar credenciais PayPal
    if (!PAYPAL_CLIENT_ID || !PAYPAL_CLIENT_SECRET) {
      return res.status(500).json({
        error: 'Credenciais PayPal não configuradas'
      });
    }
    
    // ETAPA 1: Obter token PayPal
    console.log('🔑 ETAPA 1: Obtendo token PayPal...');
    
    let accessToken;
    try {
      accessToken = await getPayPalAccessToken();
      console.log('✅ Token PayPal obtido');
    } catch (error) {
      console.error('❌ Erro ao obter token PayPal:', error.message);
      return res.status(500).json({
        error: 'Erro de autenticação PayPal. Tente novamente.',
        details: error.message
      });
    }
    
    // ETAPA 2: Capturar pagamento no PayPal
    console.log('💳 ETAPA 2: Capturando pagamento PayPal...');
    
    const captureOptions = {
      hostname: PAYPAL_BASE_URL.replace('https://', ''),
      port: 443,
      path: `/v2/checkout/orders/${orderID}/capture`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
        'Accept': 'application/json',
        'Prefer': 'return=representation'
      }
    };
    
    try {
      const captureResponse = await makePayPalRequest(captureOptions, '{}');
      
      if (captureResponse.statusCode === 201) {
        const captureResult = JSON.parse(captureResponse.body);
        console.log('✅ Pagamento PayPal capturado:', captureResult.id);
        console.log('💰 Status:', captureResult.status);
        
        // Verificar se o pagamento foi realmente completado
        if (captureResult.status === 'COMPLETED') {
          console.log('🎉 Pagamento confirmado como COMPLETED');
          
          // ETAPA 3: Atualizar status no Django
          console.log('🔄 ETAPA 3: Atualizando status no Django...');
          
          // Buscar pedido por external_reference se não tiver pedido_id
          let pedidoParaAtualizar = pedido_id;
          
          if (!pedidoParaAtualizar && external_reference) {
            try {
              const pedidoResponse = await axios.get(
                `${DJANGO_API_URL}/pedidos/referencia/${encodeURIComponent(external_reference)}/`,
                {
                  headers: {
                    'Authorization': `Token ${DJANGO_API_TOKEN}`,
                    'Accept': 'application/json'
                  }
                }
              );
              
              pedidoParaAtualizar = pedidoResponse.data.id;
              console.log('✅ Pedido encontrado por external_reference:', pedidoParaAtualizar);
              
            } catch (error) {
              console.error('❌ Erro ao buscar pedido por external_reference:', error.message);
            }
          }
          
          // Atualizar status do pedido para aprovado
          if (pedidoParaAtualizar) {
            try {
              // Extrair payment_id da resposta de captura
              const paymentId = captureResult.purchase_units?.[0]?.payments?.captures?.[0]?.id || captureResult.id;
              
              await axios.post(
                `${DJANGO_API_URL}/pedidos/${pedidoParaAtualizar}/atualizar_status/`,
                {
                  status_pagamento: 'approved',
                  payment_id: paymentId,
                  observacoes: `Pagamento PayPal capturado com sucesso. Transaction ID: ${paymentId}`
                },
                {
                  headers: {
                    'Authorization': `Token ${DJANGO_API_TOKEN}`,
                    'Content-Type': 'application/json'
                  }
                }
              );
              
              console.log('✅ Status do pedido atualizado para aprovado');
              
            } catch (error) {
              console.error('❌ Erro ao atualizar status do pedido:', error.response?.data || error.message);
              // Não bloquear o fluxo se apenas a atualização falhar
            }
          }
          
          // Retornar sucesso
          res.json({
            success: true,
            status: 'COMPLETED',
            transaction_id: captureResult.id,
            payment_id: captureResult.purchase_units?.[0]?.payments?.captures?.[0]?.id || captureResult.id,
            pedido_id: pedidoParaAtualizar,
            message: 'Pagamento processado com sucesso!'
          });
          
        } else {
          console.warn('⚠️ Pagamento não completado:', captureResult.status);
          res.status(400).json({
            success: false,
            status: captureResult.status,
            message: 'Pagamento não foi completado',
            details: captureResult
          });
        }
        
      } else {
        console.error('❌ Erro ao capturar pagamento PayPal:', captureResponse.statusCode, captureResponse.body);
        
        // Tentar parsear erro do PayPal
        let errorDetails = captureResponse.body;
        try {
          const errorData = JSON.parse(captureResponse.body);
          errorDetails = errorData.details || errorData.message || errorData;
        } catch (parseError) {
          // Manter erro original se não conseguir parsear
        }
        
        return res.status(500).json({
          success: false,
          error: 'Erro ao capturar pagamento PayPal',
          status_code: captureResponse.statusCode,
          details: errorDetails
        });
      }
      
    } catch (error) {
      console.error('❌ Erro na comunicação com PayPal:', error.message);
      return res.status(500).json({
        success: false,
        error: 'Erro ao processar captura PayPal',
        details: error.message
      });
    }
    
  } catch (error) {
    console.error('❌ Erro geral no capture-paypal-order:', error);
    res.status(500).json({
      success: false,
      error: 'Erro interno do servidor',
      message: error.message
    });
  }
});

// Endpoint para configuração de métodos de pagamento
app.get('/api/payment-config', (req, res) => {
  const config = {
    cartao: process.env.FORMA_PAGAMENTO_CARTAO || 'PAYPAL',
    pix: process.env.FORMA_PAGAMENTO_PIX || 'MERCADOPAGO'
  };
  
  console.log('🔧 Configuração de pagamentos solicitada:', config);
  
  // Validar configurações
  const validProviders = ['MERCADOPAGO', 'PAYPAL'];
  
  if (!validProviders.includes(config.cartao)) {
    console.warn(`⚠️ Provedor inválido para cartão: ${config.cartao}. Usando PAYPAL como padrão.`);
    config.cartao = 'PAYPAL';
  }
  
  if (!validProviders.includes(config.pix)) {
    console.warn(`⚠️ Provedor inválido para PIX: ${config.pix}. Usando MERCADOPAGO como padrão.`);
    config.pix = 'MERCADOPAGO';
  }
  
  // Verificar se PIX está configurado para PayPal (não suportado)
  if (config.pix === 'PAYPAL') {
    console.warn('⚠️ PIX não é suportado pelo PayPal. Forçando MERCADOPAGO para PIX.');
    config.pix = 'MERCADOPAGO';
  }
  
  // Verificar se os provedores estão configurados
  const status = {
    mercadopago_configured: !!process.env.MERCADOPAGO_ACCESS_TOKEN,
    paypal_configured: !!(process.env.PAYPAL_CLIENT_ID && process.env.PAYPAL_CLIENT_SECRET),
    django_configured: !!process.env.DJANGO_API_TOKEN
  };
  
  console.log('🔍 Status dos provedores:', status);
  
  res.json({
    config,
    status,
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
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