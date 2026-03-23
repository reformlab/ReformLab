# Deployment Guide — Kamal 2 + Hetzner

This guide covers deploying ReformLab (FastAPI backend + React frontend) to a Hetzner VPS using Kamal 2.

## Overview

```
git push origin master → GitHub Actions → kamal deploy → Hetzner VPS
```

- **Kamal 2**: Docker-based deployment tool. Builds images, pushes to registry, deploys via SSH, manages Traefik reverse proxy with automatic HTTPS.
- **Hetzner CX22**: 2 vCPU, 4 GB RAM, 40 GB SSD, ~3.29 EUR/month. EU datacenter (Germany).
- **Traefik**: Reverse proxy managed by Kamal. Automatic Let's Encrypt certificates.
- **GitHub Container Registry (ghcr.io)**: Docker image storage.

Total cost: ~4.29 EUR/month (server + domain).

## Prerequisites

- Docker installed locally
- Ruby installed locally (Kamal is a Ruby gem)
- A GitHub account with the repository
- A domain name (e.g., `reformlab.fr`) with DNS access

## Step 1: Install Kamal (5 min)

```bash
gem install kamal
kamal version
# Should show 2.x
```

## Step 2: Create a Hetzner Server (10 min)

1. Create an account at [hetzner.com/cloud](https://www.hetzner.com/cloud)
2. Create a new project called `reformlab`
3. Add your SSH public key: **Security > SSH Keys > Add SSH Key**
4. Create a server:
   - **Location:** Falkenstein (fsn1) or Nuremberg (nbg1)
   - **Image:** Ubuntu 24.04
   - **Type:** CX22 (2 vCPU, 4 GB RAM, 40 GB SSD) — 3.29 EUR/month
   - **SSH Key:** select the key you added
   - **Name:** `reformlab`
5. Note the server's **public IPv4 address** (e.g., `65.21.xxx.xxx`)

## Step 3: Point DNS to Server (5 min)

At your domain registrar, create two A records:

| Type | Name | Value | TTL |
| --- | --- | --- | --- |
| A | api | 65.21.xxx.xxx | 300 |
| A | app | 65.21.xxx.xxx | 300 |

Wait a few minutes for propagation.

## Step 4: Create a GitHub Personal Access Token (5 min)

Kamal uses GitHub Container Registry (ghcr.io) to store Docker images.

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Generate a **classic** token with `write:packages` and `read:packages` scopes
3. Save the token — you will need it in the next step

## Step 5: Configure Kamal (15 min)

### Kamal secrets

Create `.kamal/secrets` (this file is gitignored):

```bash
KAMAL_REGISTRY_PASSWORD=ghp_your_github_token_here
AUTH_PASSWORD=your_shared_password_for_colleagues
```

### Kamal deploy config

Create `config/deploy.yml`:

```yaml
service: reformlab

image: your-github-username/reformlab

servers:
  web:
    hosts:
      - 65.21.xxx.xxx
    labels:
      traefik.http.routers.reformlab-api.rule: Host(`api.reformlab.fr`)
      traefik.http.routers.reformlab-api.tls: true
      traefik.http.routers.reformlab-api.tls.certresolver: letsencrypt
    options:
      network: private

proxy:
  ssl: true
  host: api.reformlab.fr

registry:
  server: ghcr.io
  username: your-github-username
  password:
    - KAMAL_REGISTRY_PASSWORD

builder:
  arch: amd64

volumes:
  - /data/reformlab:/app/data

env:
  clear:
    REFORMLAB_DATA_DIR: /app/data
  secret:
    - AUTH_PASSWORD

accessories:
  frontend:
    image: your-github-username/reformlab-frontend
    host: 65.21.xxx.xxx
    port: 8080
    dockerfile: frontend/Dockerfile
    labels:
      traefik.http.routers.reformlab-app.rule: Host(`app.reformlab.fr`)
      traefik.http.routers.reformlab-app.tls: true
      traefik.http.routers.reformlab-app.tls.certresolver: letsencrypt
```

Replace:
- `65.21.xxx.xxx` with your Hetzner server IP
- `your-github-username` with your GitHub username
- `api.reformlab.fr` / `app.reformlab.fr` with your actual domains

### Backend Dockerfile

Create `Dockerfile` at project root:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ ./src/

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.reformlab.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

Create `frontend/Dockerfile`:

```dockerfile
FROM node:22-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
```

### Frontend nginx config

Create `frontend/nginx.conf`:

```nginx
server {
    listen 8080;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## Step 6: First Deploy (10 min)

```bash
# Initial setup — installs Docker on the server, starts Traefik
kamal setup

# Deploy both services
kamal deploy
```

Kamal will:
1. SSH into the Hetzner server
2. Install Docker (if not present)
3. Start Traefik with Let's Encrypt
4. Build the backend Docker image
5. Push it to ghcr.io
6. Pull and run it on the server
7. Start the frontend accessory
8. Perform health checks
9. Switch traffic to the new containers (zero-downtime)

Visit `https://app.reformlab.fr` — your frontend should be live.
Visit `https://api.reformlab.fr/health` — your backend should respond.

## Step 7: Set Up GitHub Actions Auto-Deploy (10 min)

### Add GitHub repository secrets

Go to your repo > **Settings > Secrets and variables > Actions** and add:

| Secret | Value |
| --- | --- |
| `KAMAL_REGISTRY_PASSWORD` | Your GitHub personal access token |
| `AUTH_PASSWORD` | The shared password for colleagues |
| `SSH_PRIVATE_KEY` | Your SSH private key (the one whose public key is on Hetzner) |

### Create the workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [master]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Ruby
        uses: ruby/setup-ruby@v1
        with:
          ruby-version: "3.3"

      - name: Install Kamal
        run: gem install kamal

      - name: Set up SSH key
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan -H 65.21.xxx.xxx >> ~/.ssh/known_hosts

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Deploy with Kamal
        env:
          KAMAL_REGISTRY_PASSWORD: ${{ secrets.KAMAL_REGISTRY_PASSWORD }}
          AUTH_PASSWORD: ${{ secrets.AUTH_PASSWORD }}
        run: kamal deploy
```

Replace `65.21.xxx.xxx` with your server IP.

After this, every `git push origin master` automatically deploys.

## Daily Operations

### Deploy manually

```bash
kamal deploy
```

### Rollback to previous version

```bash
kamal rollback
```

### View logs

```bash
# Backend logs
kamal app logs

# Frontend logs
kamal accessory logs frontend

# Traefik logs
kamal traefik logs
```

### Open a console on the server

```bash
kamal app exec -i bash
```

### Check running containers

```bash
kamal details
```

### Restart services

```bash
kamal app boot        # restart backend
kamal accessory boot frontend  # restart frontend
```

## Monitoring

Two lightweight dashboards are deployed as Kamal accessories:

- **Dozzle** — real-time Docker log viewer: `https://logs.reform-lab.eu`
  - Login: `admin` / same password as `REFORMLAB_PASSWORD`
  - Shows logs from all containers (backend, frontend, website, Traefik)
  - Search, filter, and tail logs in the browser

- **Glances** — system monitoring dashboard: `https://monitor.reform-lab.eu`
  - Shows CPU, RAM, disk, network, and per-container stats
  - No authentication (read-only system metrics)

### Monitoring CLI

```bash
# Reboot monitoring accessories
kamal accessory reboot dozzle
kamal accessory reboot glances

# View monitoring logs
kamal accessory logs dozzle
kamal accessory logs glances
```

### DNS setup for monitoring

Add these A records pointing to `<YOUR_SERVER_IP>`:

| Type | Name | Value |
| --- | --- | --- |
| A | logs | <YOUR_SERVER_IP> |
| A | monitor | <YOUR_SERVER_IP> |

Traefik will handle HTTPS certificates automatically once DNS propagates.

## Backup

The data directory `/data/reformlab` on the Hetzner server contains all scenario configs, run outputs, and manifests. Back it up periodically:

```bash
# From your local machine
ssh root@65.21.xxx.xxx "tar czf /tmp/reformlab-backup.tar.gz /data/reformlab"
scp root@65.21.xxx.xxx:/tmp/reformlab-backup.tar.gz ./backups/

# Or use Hetzner snapshots (automated, 0.012 EUR/GB/month)
```

## Troubleshooting

### HTTPS certificates not working

Traefik needs DNS to resolve to your server IP. Check:

```bash
dig api.reformlab.fr
dig app.reformlab.fr
```

Both should return your Hetzner IP. Certificates are issued automatically once DNS propagates.

### Container won't start

```bash
kamal app logs --since 5m
```

Check for Python import errors, missing environment variables, or port conflicts.

### Disk full

```bash
ssh root@65.21.xxx.xxx df -h
```

The CX22 has 40 GB. If data grows beyond that, either upgrade the server or add a Hetzner volume (block storage, from 0.052 EUR/GB/month).

### Migration to a different provider

Kamal deploys to any Linux server via SSH. To migrate:

1. Provision a new server (any provider)
2. Add your SSH key to it
3. Change the IP in `config/deploy.yml`
4. Run `kamal setup && kamal deploy`
5. Update DNS records
