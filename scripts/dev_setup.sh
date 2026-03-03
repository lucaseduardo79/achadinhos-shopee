#!/bin/bash

# Script de setup para ambiente de desenvolvimento

set -e

echo "================================================"
echo "Setup do Ambiente de Desenvolvimento"
echo "================================================"

# Verifica Python
echo "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ $PYTHON_VERSION encontrado"

# Cria ambiente virtual
echo ""
echo "Criando ambiente virtual..."
python3 -m venv venv
echo "✅ Ambiente virtual criado"

# Ativa ambiente virtual
echo ""
echo "Ativando ambiente virtual..."
source venv/bin/activate || source venv/Scripts/activate
echo "✅ Ambiente virtual ativado"

# Instala dependências
echo ""
echo "Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependências instaladas"

# Cria arquivo .env se não existir
if [ ! -f .env ]; then
    echo ""
    echo "Criando arquivo .env..."
    cp .env.example .env
    echo "✅ Arquivo .env criado"
    echo ""
    echo "⚠️  IMPORTANTE: Configure suas credenciais no arquivo .env"
else
    echo ""
    echo "ℹ️  Arquivo .env já existe"
fi

# Cria diretório de logs
mkdir -p logs
echo "✅ Diretório de logs criado"

echo ""
echo "================================================"
echo "✅ Setup concluído com sucesso!"
echo "================================================"
echo ""
echo "Próximos passos:"
echo "1. Configure suas credenciais no arquivo .env"
echo "2. Ative o ambiente virtual: source venv/bin/activate"
echo "3. Execute a aplicação: python -m app.main"
echo ""
