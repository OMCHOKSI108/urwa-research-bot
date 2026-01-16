# 🐳 Docker Deployment Guide

## Quick Start

### Prerequisites
- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0+

### 1. Setup Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

**Required:**
- `GROQ_API_KEY` - Get free key from https://console.groq.com

**Recommended:**
- `GOOGLE_API_KEY` - Get from https://makersuite.google.com/app/apikey

### 2. Build and Run

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 3. Access the API

- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/system/health

## Docker Commands

### Basic Operations

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f urwa-brain

# Check health
curl http://localhost:8000/api/v1/system/health
```

### Advanced Operations

```bash
# Rebuild after code changes
docker-compose up -d --build

# Remove everything (including volumes)
docker-compose down -v

# Execute command inside container
docker-compose exec urwa-brain bash

# View resource usage
docker stats urwa-brain
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | - | **Required** - Groq LLM API key |
| `GOOGLE_API_KEY` | - | Google Gemini API key |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `RATE_LIMIT` | `10` | Requests per minute per IP |
| `LLM_TOKENS_PER_HOUR` | `100000` | LLM usage limit |
| `BROWSER_MINUTES_PER_HOUR` | `60` | Browser automation limit |
| `MAX_COST_PER_HOUR` | `1.0` | Max cost per hour (USD) |

### Resource Limits

Default limits (adjustable in docker-compose.yml):
- **CPU**: 2 cores max, 0.5 cores reserved
- **Memory**: 4GB max, 1GB reserved

To adjust:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'        # Increase CPU
      memory: 8G       # Increase memory
```

### Persistent Data

Data is stored in Docker volumes:
- `urwa_sessions` - User sessions
- `urwa_exports` - Exported data
- `urwa_evidence` - Scraping evidence
- `urwa_logs` - Application logs

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs urwa-brain

# Common issues:
# 1. Missing API keys - Add to .env file
# 2. Port 8000 in use - Change in docker-compose.yml
# 3. Insufficient memory - Adjust resource limits
```

### Health check failing

```bash
# Check endpoint directly
docker-compose exec urwa-brain curl http://localhost:8000/api/v1/system/health

# Restart if needed
docker-compose restart urwa-brain
```

### Playwright browser issues

```bash
# Rebuild with no cache
docker-compose build --no-cache

# Verify Playwright installation
docker-compose exec urwa-brain playwright --version
```

### Performance issues

```bash
# Check resource usage
docker stats urwa-brain

# Increase limits in docker-compose.yml if needed
# Monitor logs for memory/CPU warnings
docker-compose logs -f | grep -i "memory\|cpu"
```

## Production Deployment

### Security Best Practices

1. **Use secrets management:**
   ```bash
   # Use Docker secrets instead of .env file
   docker secret create groq_key /path/to/key
   ```

2. **Enable HTTPS:**
   - Add reverse proxy (nginx/traefik)
   - Use Let's Encrypt certificates

3. **Restrict network access:**
   ```yaml
   networks:
     urwa-network:
       internal: true
   ```

4. **Regular updates:**
   ```bash
   # Pull latest image
   docker-compose pull
   docker-compose up -d
   ```

### Monitoring

```bash
# Container health
docker inspect --format='{{.State.Health.Status}}' urwa-brain

# Resource usage
docker stats --no-stream urwa-brain

# Application metrics
curl http://localhost:8000/api/v1/system/metrics
```

### Backup

```bash
# Backup volumes
docker run --rm -v urwa_sessions:/data -v $(pwd):/backup alpine \
  tar czf /backup/urwa-backup-$(date +%Y%m%d).tar.gz /data

# Restore volumes
docker run --rm -v urwa_sessions:/data -v $(pwd):/backup alpine \
  tar xzf /backup/urwa-backup-20240116.tar.gz -C /
```

## Scaling

### Horizontal Scaling

```yaml
services:
  urwa-brain:
    deploy:
      replicas: 3  # Run 3 instances
    # Add load balancer
```

### With Load Balancer

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - urwa-brain
  
  urwa-brain:
    deploy:
      replicas: 3
    # No exposed ports - only nginx
```

## Support

- **Issues**: https://github.com/OMCHOKSI108/urwa-research-bot/issues
- **Docs**: http://localhost:8000/docs (when running)
- **Health**: http://localhost:8000/api/v1/system/health
