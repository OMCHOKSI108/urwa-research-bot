# ================================================================================
#                         URWA BRAIN - DOCKERFILE
#              Production-Grade AI Web Intelligence Platform
# ================================================================================

# Use Python 3.11 slim as base (good balance of size and compatibility)
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    # Playwright settings
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    # App settings
    HOST=0.0.0.0 \
    PORT=8000

# Set working directory
WORKDIR /app

# Install system dependencies required for Playwright and general operation
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Core utilities
    curl \
    wget \
    gnupg \
    ca-certificates \
    # Playwright dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libatspi2.0-0 \
    libgtk-3-0 \
    # Fonts
    fonts-liberation \
    fonts-noto-color-emoji \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers
RUN pip install --no-cache-dir playwright && \
    playwright install chromium && \
    playwright install-deps chromium

# Copy application code
COPY backend/app ./app
COPY backend/run.py .

# Create directories for static files and logs
RUN mkdir -p /app/app/static/sessions \
             /app/app/static/exports \
             /app/app/static/evidence \
             /app/app/static/logs \
             /app/app/static/browser_profiles

# Create non-root user for security
RUN groupadd --gid 1000 urwa && \
    useradd --uid 1000 --gid urwa --shell /bin/bash --create-home urwa && \
    chown -R urwa:urwa /app /ms-playwright

# Switch to non-root user
USER urwa

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "run.py"]
