#!/bin/bash

# Script para executar a aplicação com Docker

set -e

echo "================================================"
echo "Executando com Docker"
echo "================================================"

# Verifica se .env existe
if [ ! -f .env ]; then
    echo "❌ Arquivo .env não encontrado"
    echo "   Crie o arquivo .env baseado em .env.example"
    exit 1
fi

# Verifica se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker não está rodando"
    echo "   Inicie o Docker e tente novamente"
    exit 1
fi

echo "✅ Docker está rodando"
echo ""

# Build da imagem
echo "Construindo imagem Docker..."
docker-compose build
echo "✅ Imagem construída"
echo ""

# Executa container
echo "Iniciando container..."
docker-compose up

# Alternativas:
# docker-compose up -d  # Rodar em background
# docker-compose logs -f  # Ver logs
# docker-compose down  # Parar e remover containers
