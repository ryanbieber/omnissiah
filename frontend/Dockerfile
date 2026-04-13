# Simple development image
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with retry and timeout settings
RUN npm config set fetch-timeout 300000 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm install --legacy-peer-deps --verbose || npm install --legacy-peer-deps --verbose || npm install --legacy-peer-deps

# Copy source code
COPY . .

EXPOSE 3000

CMD ["npm", "start"]
