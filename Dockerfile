# Multi-stage build para aplicação completa ONE WAY
FROM node:18-alpine AS nodejs-builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY server.js products.json ./

# Stage 2: Python/Django
FROM python:3.11-slim AS django-builder

WORKDIR /app
COPY django_admin/ ./
RUN pip install --no-cache-dir -r requirements.txt
RUN python manage.py collectstatic --noinput
RUN python manage.py migrate  
RUN python criar_dados_exemplo.py

# Stage 3: Nginx + Aplicação final
FROM nginx:alpine

# Install supervisor para gerenciar múltiplos processos
RUN apk add --no-cache supervisor python3 py3-pip nodejs npm curl

# Criar diretórios
WORKDIR /app
RUN mkdir -p /var/log/supervisor

# Copiar configurações
COPY nginx.conf /etc/nginx/nginx.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copiar aplicações
COPY --from=nodejs-builder /app /app/nodejs
COPY --from=django-builder /app /app/django

# Copiar site estático para nginx
COPY index.html /usr/share/nginx/html/
COPY Css/ /usr/share/nginx/html/Css/
COPY img/ /usr/share/nginx/html/img/
COPY videos/ /usr/share/nginx/html/videos/
COPY *.html /usr/share/nginx/html/
COPY products.json /usr/share/nginx/html/

# Instalar dependências Python no container final
RUN pip3 install --no-cache-dir -r /app/django/requirements.txt

# Exposição de porta
EXPOSE 80

# Comando para iniciar supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]