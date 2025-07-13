const express = require('express');
const cors = require('cors');
const path = require('path');
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