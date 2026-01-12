FROM python:3.14-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md /app/
COPY highcommand/ /app/highcommand/
# Install Python dependencies with HTTP support for Kubernetes deployment
RUN pip install --no-cache-dir -e ".[http]"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run MCP server
ENTRYPOINT ["python", "-m", "highcommand.server"]
