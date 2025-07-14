# Multi-stage build para Railway
FROM node:18-alpine as nodejs

# Install curl for health checks
RUN apk add --no-cache curl

# Node.js setup
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY server.js .
COPY products.json .
COPY index.html .
COPY Css/ ./Css/
COPY img/ ./img/

# Expose Node.js port  
EXPOSE $PORT
EXPOSE 3000

# Health check for Node.js
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT:-3000}/health || exit 1

# Start Node.js (Railway will run this)
CMD ["node", "server.js"]