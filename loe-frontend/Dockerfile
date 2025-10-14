# Build
FROM node:20 AS build
WORKDIR /app
COPY loe-frontend/package*.json ./
RUN npm ci
COPY loe-frontend/ ./
RUN npm run build  # Vite -> /App/dist

# Serve
FROM nginx:1.27-alpine
COPY loe-frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
