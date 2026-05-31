# Frontend Angular — nginx alpine runtime
# Sin # syntax= ni --mount=cache: más estable en Docker Desktop/Windows

FROM node:20-alpine AS builder

WORKDIR /app

# En `docker compose build`, Compose inyecta el valor del `.env` raíz (puede ser vacío en prod).
ARG MAILHOG_WEB_URL=
ENV MAILHOG_WEB_URL=$MAILHOG_WEB_URL

COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps

COPY . .
RUN npm run build -- --configuration production

# ── Stage 2: Servidor nginx ───────────────────────────────
FROM nginx:alpine AS runtime

# Copiar build de Angular al directorio de nginx
COPY --from=builder /app/dist/emergencias-frontend/browser /usr/share/nginx/html

# Plantilla nginx (envsubst): BACKEND_UPSTREAM desde compose / runtime
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
