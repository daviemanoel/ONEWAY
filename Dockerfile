# Dockerfile unificado para Railway - Django + Node.js
FROM python:3.11-slim

# Install Node.js e outras dependências
RUN apt-get update && apt-get install -y \
    curl \
    supervisor \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy e instalar dependências Python (Django)
COPY django_admin/requirements.txt ./django_requirements.txt
RUN pip install --no-cache-dir -r django_requirements.txt

# Copy e instalar dependências Node.js
COPY package*.json ./
RUN npm install

# Copy arquivos Django
COPY django_admin/ ./django_admin/

# Copy arquivos Node.js e frontend
COPY server.js .
COPY products.json .
COPY index.html .
COPY Css/ ./Css/
COPY img/ ./img/

# Copy configuração supervisord
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose port
EXPOSE $PORT

# Start supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]