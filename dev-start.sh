#!/bin/bash

# Script para iniciar ambiente de desenvolvimento local
echo "🚀 Iniciando ambiente de desenvolvimento ONE WAY 2025..."

# Verificar se estamos no diretório correto
if [ ! -f "web/server.js" ] || [ ! -f "api/manage.py" ]; then
    echo "❌ Execute este script no diretório raiz do projeto ONEWAY"
    exit 1
fi

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📦 Verificando dependências...${NC}"

# Verificar Python
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python não encontrado. Instale Python 3.11+${NC}"
    exit 1
fi

# Verificar Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js não encontrado. Instale Node.js 18+${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Dependências OK${NC}"

# Setup Django
echo -e "${BLUE}🐍 Configurando Django...${NC}"
cd api

# Criar e ativar ambiente virtual Python
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🔧 Criando ambiente virtual Python...${NC}"
    python -m venv venv
    echo -e "${YELLOW}📦 Ativando venv e instalando dependências...${NC}"
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo -e "${GREEN}✅ Ambiente virtual encontrado, ativando...${NC}"
    source venv/bin/activate
fi

# Migrar banco se necessário
if [ ! -f "db.sqlite3" ]; then
    echo -e "${YELLOW}🗄️ Criando banco SQLite...${NC}"
    python manage.py migrate
    
    echo -e "${YELLOW}👤 Configurando admin (admin/oneway2025)...${NC}"
    echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@oneway.com', 'oneway2025')" | python manage.py shell
    
    echo -e "${YELLOW}📦 Populando produtos...${NC}"
    python manage.py setup_estoque_simples
fi

# Gerar token se não existir .env
cd ../web
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}🔑 Gerando token API...${NC}"
    cd ../api
    TOKEN=$(python manage.py criar_token_api | grep "Token:" | cut -d" " -f2)
    cd ../web
    
    cp .env.local .env
    sed -i "s/seu_token_aqui_gerar_com_comando/$TOKEN/g" .env
    
    echo -e "${GREEN}✅ Arquivo .env criado com token: $TOKEN${NC}"
    echo -e "${YELLOW}⚠️ Configure MERCADOPAGO_ACCESS_TOKEN no arquivo web/.env${NC}"
fi

# Instalar dependências Node.js
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Instalando dependências Node.js...${NC}"
    npm install
fi

echo -e "${GREEN}🎉 Setup completo!${NC}"
echo -e "${BLUE}📋 Para iniciar os serviços:${NC}"
echo ""
echo -e "${YELLOW}Terminal 1 - Django:${NC}"
echo "cd api && source venv/bin/activate && python manage.py runserver"
echo ""
echo -e "${YELLOW}Terminal 2 - Node.js:${NC}" 
echo "cd web && npm start"
echo ""
echo -e "${YELLOW}Terminal 3 - Frontend:${NC}"
echo "cd web && python -m http.server 8080"
echo ""
echo -e "${BLUE}💡 Dica:${NC} Para desativar o venv: ${YELLOW}deactivate${NC}"
echo ""
echo -e "${BLUE}URLs:${NC}"
echo "🌐 Site: http://localhost:8080"
echo "🔧 Admin: http://localhost:8000/admin (admin/oneway2025)"
echo "⚡ API: http://localhost:3000"
echo ""
echo -e "${YELLOW}⚠️ Não esqueça de configurar MERCADOPAGO_ACCESS_TOKEN em web/.env${NC}"