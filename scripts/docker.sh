#!/bin/bash
set -e

echo "=== AI RAG & Agent Service - Build Script ==="
echo ""

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check for docker compose command (newer Docker uses "docker compose" vs older "docker-compose")
if docker compose version &>/dev/null; then
    DOCKER_COMPOSE="docker compose"
elif docker-compose version &>/dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "ERROR: Neither 'docker compose' nor 'docker-compose' is installed."
    echo "Please install Docker Compose or upgrade Docker."
    exit 1
fi

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/python/.env" ]; then
    if [ -f "$PROJECT_ROOT/python/.env.example" ]; then
        warn ".env file not found. Creating from .env.example..."
        cp "$PROJECT_ROOT/python/.env.example" "$PROJECT_ROOT/python/.env"
        warn "Please edit python/.env and set your API keys before starting."
    else
        warn ".env file not found. You may need to create one manually."
    fi
fi

# Parse arguments
COMMAND=${1:-up}

case $COMMAND in
    up|start)
        info "Building and starting Docker containers..."
        cd "$PROJECT_ROOT"
        $DOCKER_COMPOSE up -d --build
        info "Services starting up..."
        info "  - App:      http://localhost:8000"
        info "  - API Doc:  http://localhost:8000/docs"
        info "  - Milvus:   localhost:19530"
        info "  - MySQL:    localhost:3306"
        echo ""
        info "To view logs: $DOCKER_COMPOSE logs -f app"
        ;;

    down|stop)
        info "Stopping Docker containers..."
        cd "$PROJECT_ROOT"
        $DOCKER_COMPOSE down
        info "Containers stopped."
        ;;

    restart)
        info "Restarting Docker containers..."
        cd "$PROJECT_ROOT"
        $DOCKER_COMPOSE restart
        info "Containers restarted."
        ;;

    build)
        info "Building Docker image..."
        cd "$PROJECT_ROOT/python"
        docker build -t ai-rag-agent:latest -f Dockerfile ..
        info "Image built: ai-rag-agent:latest"
        ;;

    clean)
        info "Stopping and removing containers, networks, and volumes..."
        cd "$PROJECT_ROOT"
        $DOCKER_COMPOSE down -v --rmi local
        warn "Clean complete. Note: Uploads and outputs directories were preserved."
        ;;

    logs)
        SERVICE=${2:-app}
        info "Showing logs for $SERVICE..."
        $DOCKER_COMPOSE logs -f $SERVICE
        ;;

    *)
        echo "Usage: $0 {up|down|restart|build|clean|logs}"
        echo ""
        echo "Commands:"
        echo "  up/start   - Build and start all services (default)"
        echo "  down/stop  - Stop all services"
        echo "  restart    - Restart all services"
        echo "  build      - Build Docker image only"
        echo "  clean      - Stop services and remove volumes"
        echo "  logs       - Show logs (optional: service name)"
        exit 1
        ;;
esac