FROM node:22-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci && \
    npm install --no-save \
      @rollup/rollup-linux-arm64-gnu@4.59.0 \
      lightningcss-linux-arm64-gnu@1.31.1 \
      @tailwindcss/oxide-linux-arm64-gnu@4.2.1
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget -q --spider http://127.0.0.1:8080/ || exit 1
