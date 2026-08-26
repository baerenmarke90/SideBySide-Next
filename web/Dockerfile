# syntax=docker/dockerfile:1.7

FROM node:26.6.0-bookworm-slim@sha256:81502e860176e63695d769d3d1a2d3a403abc1c27c6a02169b765f3e43b60ede AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .
ARG VITE_SBS_API_BASE_URL=""
ARG VITE_SBS_SPACE_ID=""
ENV VITE_SBS_API_BASE_URL=${VITE_SBS_API_BASE_URL}
ENV VITE_SBS_SPACE_ID=${VITE_SBS_SPACE_ID}
RUN npm run build

FROM ghcr.io/nginx/nginx-unprivileged:1.31.4@sha256:197f252f060ed357f2ab98d4256762d7d107c76f18ad8f0b9d5178854611566d

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=5s \
  CMD ["curl", "--fail", "--silent", "--show-error", "http://127.0.0.1:8080/healthz"]
