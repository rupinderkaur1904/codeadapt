# Reverse proxy image: Caddy (TLS, HSTS, headers) serving the static web build and
# proxying /api to the API container (ADR-042, Milestone 3). Build from the repo root:
#   docker build -f deploy/web.Dockerfile -t codeadapt-proxy:<tag> .
FROM node:22-alpine@sha256:0e1754758c2df4cfa3e68d59e2e1b7374bb7fd9ea6328eaaacf15cc934af8202 AS build
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

FROM caddy:2.8.4-alpine@sha256:af32e97399febea808609119bb21544d0265c58a02836576e32a2d082c262c17
COPY deploy/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /web/dist /srv
