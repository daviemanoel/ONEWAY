# SETUP AMBIENTE DE DESENVOLVIMENTO LOCAL

## Pré-requisitos
- Python 3.11+
- Node.js 18+
- Git

## 1. Setup Django Local (SQLite)

```bash
# Navegar para API
cd api

# Instalar dependências Python
pip install -r requirements.txt

# Criar banco SQLite local
python manage.py migrate

# Criar usuário admin
python manage.py createsuperuser
# Usuário: admin
# Senha: oneway2025

# Popular produtos no banco local
python manage.py setup_estoque_simples

# Gerar token para Node.js
python manage.py criar_token_api
# ⚠️ COPIAR O TOKEN GERADO

# Iniciar servidor Django
python manage.py runserver
```

✅ **Django Admin**: http://localhost:8000/admin

## 2. Setup Node.js Local

```bash
# Nova aba do terminal
cd web

# Instalar dependências Node.js
npm install

# Criar arquivo .env (copiar .env.local)
cp .env.local .env

# Editar .env com o token gerado acima
nano .env
# Alterar linha: DJANGO_API_TOKEN=token_copiado_do_comando_acima

# Iniciar servidor Node.js
npm start
```

✅ **API Node.js**: http://localhost:3000

## 3. Setup Frontend Local

```bash
# Nova aba do terminal
cd web

# Servir arquivos estáticos
python -m http.server 8080
```

✅ **Site**: http://localhost:8080

## 4. Variáveis de Ambiente

Edite o arquivo `web/.env` com os valores corretos:

```env
# Token gerado no passo 1
DJANGO_API_TOKEN=token_gerado_criar_token_api

# Tokens do Mercado Pago (copiar do Railway produção)
MERCADOPAGO_ACCESS_TOKEN=APP_USR_xxxxx
```

## 5. Teste Completo

1. **Abrir site**: http://localhost:8080
2. **Adicionar produto ao carrinho**
3. **Finalizar compra** (usará MP produção)
4. **Verificar pedido no admin**: http://localhost:8000/admin

## Benefícios

- ✅ Dados isolados em SQLite local
- ✅ Admin Django funcionando localmente  
- ✅ Pagamentos MP produção funcionando
- ✅ Desenvolvimento sem afetar produção
- ✅ Testes seguros de novas funcionalidades

## Comandos Úteis

```bash
# Resetar banco local
rm api/db.sqlite3
python manage.py migrate
python manage.py createsuperuser

# Ver logs Django
python manage.py runserver --verbosity=2

# Ver logs Node.js
npm start

# Gerar novo token
python manage.py criar_token_api
```

## Estrutura Desenvolvimento

```
http://localhost:8080  → Frontend HTML/CSS/JS
         ↓
http://localhost:3000  → Backend Node.js (APIs pagamento)
         ↓  
http://localhost:8000  → Django Admin (banco SQLite)
         ↓
MP Produção           → Pagamentos reais (sandbox opcional)
```