# 🐳 ONE WAY - Arquitetura Docker Unificada

Sistema completo ONE WAY 2025 em um único container Docker com múltiplos serviços.

## 🏗️ **Arquitetura**

```
🌐 Nginx (Proxy Reverso - Porta 80)
├── /          → 📄 Site Estático (index.html)
├── /admin/    → 🐍 Django Admin
├── /api/      → 🟢 Node.js API  
└── /static/   → 📦 Assets Django
```

## 📋 **Componentes**

### **1. Nginx (Porta 80)**
- Proxy reverso para roteamento
- Serve arquivos estáticos do site
- Redireciona `/admin/` → Django
- Redireciona `/api/` → Node.js

### **2. Django Admin (Porta 8000)**
- Sistema de gestão de pedidos
- Interface admin completa
- Banco SQLite integrado
- Dados de exemplo pré-carregados

### **3. Node.js API (Porta 3000)**
- Processamento pagamentos Mercado Pago
- Endpoints: `/create-mp-checkout`, `/mp-health`
- Integração com products.json

### **4. Site Estático**
- Frontend ONE WAY (HTML/CSS/JS)
- Todas as páginas: index, success, cancel
- Imagens, vídeos e assets

## 🚀 **Deploy Railway**

### **Automatizado via Dockerfile**
```dockerfile
# Multi-stage build:
# 1. Build Node.js
# 2. Build Django  
# 3. Nginx + Supervisor
```

### **Supervisor gerencia:**
- ✅ Nginx (proxy)
- ✅ Django (admin)
- ✅ Node.js (API)

## 🔗 **URLs Funcionais**

```bash
https://oneway-production.up.railway.app/
├── /                    → Site ONE WAY
├── /admin/              → Django Admin (admin/admin123)
├── /create-mp-checkout  → API pagamentos MP
├── /mp-success.html     → Sucesso MP com dados
├── /mp-cancel.html      → Cancel MP
└── /health              → Health check
```

## ✅ **Vantagens**

1. **Monolito Simplificado**: Tudo em um lugar
2. **URLs Limpas**: Sem conflitos de rotas
3. **Deploy Único**: Um só projeto Railway
4. **Performance**: Nginx otimizado
5. **Manutenção**: Arquitetura organizada

## 🔧 **Configuração**

### **Variáveis de Ambiente (Railway)**
```bash
STRIPE_SECRET_KEY=sk_live_...
MERCADOPAGO_ACCESS_TOKEN=APP_USR_...
DJANGO_SECRET_KEY=sua-chave-personalizada
DEBUG=False
```

### **Health Check**
- **Path**: `/health`
- **Timeout**: 100s
- **Retries**: 10

## 📊 **Monitoramento**

### **Logs Separados**
- `/var/log/supervisor/nginx.out.log`
- `/var/log/supervisor/django.out.log`  
- `/var/log/supervisor/nodejs.out.log`

### **Processos Supervisionados**
```bash
supervisorctl status
# nginx    RUNNING
# django   RUNNING  
# nodejs   RUNNING
```

## 🎯 **Resultado**

- ✅ Site ONE WAY funcionando na raiz
- ✅ Django Admin em `/admin/`
- ✅ API pagamentos MP funcionando
- ✅ Todos os assets carregando
- ✅ Deploy unificado Railway

**Arquitetura completa, organizada e escalável!** 🚀