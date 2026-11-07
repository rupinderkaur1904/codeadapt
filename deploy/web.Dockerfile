# Reverse proxy image: Caddy (TLS, HSTS, headers) serving the static web build and
# proxying /api to the API container (ADR-042, Milestone 3). Build from the repo root:
#   docker build -f deploy/web.Dockerfile -t codeadapt-proxy:<tag> .
FROM node:22-alpine AS build
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

FROM caddy:2.8.4-alpine
COPY deploy/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /web/dist /srv
