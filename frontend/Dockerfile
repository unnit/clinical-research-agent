# ---- Build stage ----
FROM node:20-alpine AS build

WORKDIR /app

# Install deps first for better layer caching
COPY package.json package-lock.json* ./
RUN npm ci

# Build args — Vite reads VITE_* env vars at build time
ARG VITE_API_BASE=/api
ENV VITE_API_BASE=$VITE_API_BASE

# Copy source and build
COPY . .
RUN npm run build

# ---- Serve stage ----
FROM nginx:alpine

# Replace the default nginx config with one suited for SPA + SSE
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built static files
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
