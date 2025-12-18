FROM python:3.12

# Create non-root user
RUN addgroup -g 1000 ansys && \
	adduser -D -u 1000 -G ansys -s /bin/sh ansys && \
	mkdir -p /app /workspace && \
	chown -R ansys:ansys /app /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install the package with git credentials
# Use BuildKit secrets to securely pass GitHub token
RUN --mount=type=secret,id=github_token \
    if [ -f /run/secrets/github_token ]; then \
        export GH_TOKEN=$(cat /run/secrets/github_token) && \
        git config --global url."https://${GH_TOKEN}@github.com/".insteadOf "https://github.com/" && \
        pip install --no-cache-dir --upgrade pip && \
        pip install --no-cache-dir -e . && \
        git config --global --unset url."https://${GH_TOKEN}@github.com/".insteadOf; \
    else \
        echo "Warning: No GitHub token provided, attempting installation anyway..." && \
        pip install --no-cache-dir --upgrade pip && \
        pip install --no-cache-dir -e .; \
    fi

# Set default environment variables
ENV PYMAPDL_START_INSTANCE=false
ENV PYMAPDL_IP=host.docker.internal
ENV PYMAPDL_PORT=50052

ENV HTTP_HOST=0.0.0.0
ENV HTTP_PORT=8080

# Expose the ports
EXPOSE ${HTTP_PORT}
EXPOSE ${PYMAPDL_PORT}

# Create entrypoint
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Starting PyMAPDL MCP Server with HTTP transport..."\n\
echo "MAPDL connection: $PYMAPDL_IP:$PYMAPDL_PORT"\n\
echo "HTTP server: $HTTP_HOST:$HTTP_PORT"\n\
\n\
# Start the MCP server with HTTP transport\n\
exec ansys-mapdl-mcp \\\n\
    --connect-on-startup \\\n\
    --transport http \\\n\
    --ip "$PYMAPDL_IP" \\\n\
    --port "$PYMAPDL_PORT" \\\n\
    --http-host "$HTTP_HOST" \\\n\
    --http-port "$HTTP_PORT"\n\
' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
