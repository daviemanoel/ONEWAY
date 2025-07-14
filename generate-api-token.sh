#!/bin/bash
# Script para gerar token da API Django no Railway

echo "🚀 Gerando token da API Django..."

# Executar comando Django para criar token
docker-compose exec django python manage.py criar_token_api --username api_nodejs_railway

echo ""
echo "📋 Copie o token gerado e adicione nas Environment Variables do Railway:"
echo "DJANGO_API_TOKEN=<token_gerado>"