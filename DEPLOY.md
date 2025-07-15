# Deploy e Configuração - ONE WAY 2025

Guia completo para deploy e configuração do sistema ONE WAY 2025 no Railway com domínio personalizado.

## 🚀 Visão Geral

O projeto utiliza **Railway** como plataforma de deploy com dois services separados:
- **Frontend + Backend Node.js** (`/web`) → `oneway.mevamfranca.com.br`
- **Django Admin + API** (`/api`) → `api.oneway.mevamfranca.com.br`

## 🏗️ Arquitetura de Deploy

```
GitHub Repository (main branch)
         ↓
    Railway Auto-Deploy
         ↓
┌────────────────────┬─────────────────────┐
│   WEB Service      │    API Service      │
│   Node.js/Express  │    Django/DRF       │
│   /web directory   │    /api directory   │
│   Port 3000        │    Port 8000        │
└────────────────────┴─────────────────────┘
         ↓                      ↓
    Custom Domain          Custom Domain
    vec1sgfe.up            zbuqcy69.up
    railway.app            railway.app
         ↓                      ↓
    oneway.mevamfranca     api.oneway.mevam
    .com.br                franca.com.br
```

## 🔧 Configuração Railway

### 1. Criação dos Services

#### WEB Service (Frontend + Backend Node.js)
```bash
# Configurações Railway WEB
Root Directory: /web
Build Command: npm install
Start Command: npm start
Port: 3000
Auto-Deploy: true (main branch)
```

#### API Service (Django Admin)
```bash
# Configurações Railway API
Root Directory: /api
Build Command: pip install -r requirements.txt
Start Command: gunicorn oneway_admin.wsgi:application
Port: 8000
Auto-Deploy: true (main branch)
```

### 2. Variáveis de Ambiente

#### WEB Service (Node.js)
```bash
# Mercado Pago
MERCADOPAGO_ACCESS_TOKEN=APP_USR_xxx
MERCADOPAGO_PUBLIC_KEY=APP_USR_xxx

# Django Integration
DJANGO_API_URL=https://api.oneway.mevamfranca.com.br/api
DJANGO_API_TOKEN=xxx

# URLs de Retorno
MP_SUCCESS_URL=https://oneway.mevamfranca.com.br/mp-success
MP_CANCEL_URL=https://oneway.mevamfranca.com.br/mp-cancel

# Configurações
NODE_ENV=production
PORT=3000
```

#### API Service (Django)
```bash
# Database (Auto-configurado pelo Railway)
DATABASE_URL=postgresql://user:pass@host:port/db

# Django
DJANGO_SECRET_KEY=xxx
DEBUG=False
ALLOWED_HOSTS=api.oneway.mevamfranca.com.br,oneway.mevamfranca.com.br

# Mercado Pago (para consultas admin)
MERCADOPAGO_ACCESS_TOKEN=APP_USR_xxx

# Static Files
STATIC_URL=/static/
STATIC_ROOT=/app/staticfiles/
```

### 3. Custom Domains

#### Configuração Railway
1. **WEB Service** → Settings → Domains → Add Domain
   - Domain: `oneway.mevamfranca.com.br`
   - CNAME Target: `vec1sgfe.up.railway.app`

2. **API Service** → Settings → Domains → Add Domain
   - Domain: `api.oneway.mevamfranca.com.br`
   - CNAME Target: `zbuqcy69.up.railway.app`

#### Configuração DNS (Locaweb)
```dns
# Frontend
Tipo: CNAME
Nome: oneway
Conteúdo: vec1sgfe.up.railway.app
TTL: 3600

# API
Tipo: CNAME
Nome: api.oneway
Conteúdo: zbuqcy69.up.railway.app
TTL: 3600
```

## 🗄️ Banco de Dados

### PostgreSQL Railway
- **Tipo**: PostgreSQL 15+
- **Backup**: Automático
- **Conexão**: Via DATABASE_URL
- **Persistência**: Dados mantidos entre deploys

### Configuração Híbrida
```python
# api/oneway_admin/settings.py
import dj_database_url

if os.environ.get('DATABASE_URL'):
    # Produção: PostgreSQL Railway
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
    }
else:
    # Local: SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
```

### Setup Inicial
```bash
# Comando customizado para setup automático
python manage.py setup_database

# Cria:
# - Todas as tabelas
# - Superuser (admin/oneway2025)
# - Token API para Node.js
# - Configurações iniciais
```

## 🔐 Segurança

### CORS Configuration
```python
CORS_ALLOWED_ORIGINS = [
    "https://oneway.mevamfranca.com.br",
    "https://api.oneway.mevamfranca.com.br",
    "http://localhost:3000",  # Desenvolvimento
]
```

### CSRF Protection
```python
CSRF_TRUSTED_ORIGINS = [
    'https://oneway.mevamfranca.com.br',
    'https://api.oneway.mevamfranca.com.br',
    'https://*.railway.app',  # Para testes
]
```

### SSL/TLS
- **Railway**: SSL automático via Let's Encrypt
- **Força HTTPS**: Configurado automaticamente
- **HSTS**: Headers de segurança configurados

## 📦 Build Process

### Frontend (WEB Service)
```dockerfile
# Processo automático Railway
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --only=production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

### Backend (API Service)
```dockerfile
# api/Dockerfile
FROM python:3.11-slim
WORKDIR /app

# Dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY . .

# Static files
RUN python manage.py collectstatic --noinput

# Setup automático + Servidor
CMD ["sh", "-c", "python manage.py setup_database && gunicorn oneway_admin.wsgi:application --bind 0.0.0.0:8000"]
```

## 🚀 Deploy Workflow

### Processo Automático
1. **Push para main** → Trigger deploy Railway
2. **WEB Service**: Build Node.js + Deploy
3. **API Service**: Build Django + Migrate + Deploy
4. **Health Check**: Verificação automática
5. **SSL**: Renovação automática

### Deploy Manual
```bash
# Railway CLI
railway login
railway link  # Conectar ao projeto
railway up    # Deploy forçado

# Por service específico
railway up --service WEB
railway up --service API
```

## 📊 Monitoramento

### Health Checks
```bash
# Frontend
curl https://oneway.mevamfranca.com.br/health

# Backend Node.js
curl https://oneway.mevamfranca.com.br/mp-health

# Django Admin
curl https://api.oneway.mevamfranca.com.br/admin/

# API REST
curl https://api.oneway.mevamfranca.com.br/api/
```

### Logs
```bash
# Logs em tempo real
railway logs -f

# Por service
railway logs --service WEB -f
railway logs --service API -f

# Filtros
railway logs --filter "ERROR"
railway logs --filter "POST"
```

### Métricas Railway
- **CPU Usage**: < 50% normal
- **Memory**: < 512MB por service
- **Response Time**: < 500ms médio
- **Uptime**: 99.9%+

## 🛠️ Manutenção

### Comandos Úteis
```bash
# Status dos services
railway status

# Restart service
railway service restart WEB
railway service restart API

# Variáveis de ambiente
railway variables
railway variables set KEY=VALUE

# Banco de dados
railway shell --service API
python manage.py dbshell
```

### Backup
```bash
# Backup manual do banco
railway run --service API "python manage.py dumpdata > backup.json"

# Restaurar backup
railway run --service API "python manage.py loaddata backup.json"
```

### Troubleshooting
```bash
# Debug Django
railway run --service API "python manage.py shell"

# Verificar migrações
railway run --service API "python manage.py showmigrations"

# Reset database (CUIDADO!)
railway run --service API "python fix_db.py"
```

## 🔄 CI/CD Pipeline

### GitHub Integration
```yaml
# Auto-deploy configurado via Railway UI
Trigger: Push to main branch
Build: Automático
Deploy: Automático
Rollback: Manual via Railway UI
```

### Estratégia de Deploy
1. **Development**: Testes locais
2. **Staging**: Deploy automático main branch
3. **Production**: Mesmo ambiente (Railway)
4. **Rollback**: Via Railway UI se necessário

## 📈 Escalabilidade

### Resource Limits
```yaml
WEB Service:
  CPU: 1 vCPU
  Memory: 512MB
  Storage: 1GB

API Service:
  CPU: 1 vCPU
  Memory: 512MB
  Storage: 1GB
  Database: PostgreSQL (Railway managed)
```

### Auto-Scaling
- **Railway**: Auto-scale baseado na demanda
- **Database**: Conexões gerenciadas automaticamente
- **CDN**: Assets servidos via Railway Edge

## 🔍 Debugging

### Logs Importantes
```bash
# Erros de aplicação
railway logs --filter "ERROR" --service API

# Requests MP
railway logs --filter "Mercado Pago" --service WEB

# Django Admin access
railway logs --filter "admin" --service API

# Performance
railway logs --filter "slow" -f
```

### Comandos Debug
```bash
# Testar banco local
python api/test_db.py

# Verificar configuração
python api/manage.py check

# Testar API
curl -H "Authorization: Token XXX" \
     https://api.oneway.mevamfranca.com.br/api/pedidos/
```

---

## 📞 Suporte

- **Railway Console**: [railway.app](https://railway.app)
- **GitHub Issues**: [ONEWAY/issues](https://github.com/daviemanoel/ONEWAY/issues)
- **Admin Interface**: https://api.oneway.mevamfranca.com.br/admin/
- **Documentação**: README.md e CLAUDE.md

**Sistema em produção** desde julho de 2025 | Deploy automático ativo