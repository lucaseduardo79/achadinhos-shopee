# ⚡ Quick Start Guide

Comece a usar o sistema em 5 minutos!

## 🎯 Passo a Passo Rápido

### 1. Clone e Configure

```bash
# Clone o repositório
git clone <seu-repo>
cd achadinhos_shopee

# Copie o arquivo de configuração
cp .env.example .env
```

### 2. Configure Credenciais

Edite o arquivo `.env` e adicione suas credenciais:

```bash
# Mínimo necessário para funcionar
SHOPEE_API_KEY=sua_api_key
SHOPEE_API_SECRET=seu_api_secret
SHOPEE_PARTNER_ID=seu_partner_id

INSTAGRAM_ACCESS_TOKEN=seu_access_token
INSTAGRAM_ACCOUNT_ID=seu_account_id
```

### 3. Execute com Docker (Recomendado)

```bash
# Construir e executar
docker-compose up --build

# Ou use o script helper
chmod +x scripts/run_docker.sh
./scripts/run_docker.sh
```

### 4. Ou Execute Localmente

```bash
# Setup automático
chmod +x scripts/dev_setup.sh
./scripts/dev_setup.sh

# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Executar
python -m app.main
```

---

## 📋 Checklist de Setup

- [ ] Python 3.11+ instalado (se executar localmente)
- [ ] Docker instalado (se executar com Docker)
- [ ] Credenciais da Shopee configuradas no `.env`
- [ ] Credenciais do Instagram configuradas no `.env`
- [ ] Access Token do Instagram é de longa duração (60 dias)
- [ ] Conta Instagram é Business ou Creator

---

## 🔑 Como Obter Credenciais

### Shopee

1. Acesse [Shopee Open Platform](https://open.shopee.com/)
2. Crie uma conta de desenvolvedor/afiliado
3. Crie uma app
4. Copie: API Key, API Secret, Partner ID

### Instagram

1. Acesse [Meta for Developers](https://developers.facebook.com/)
2. Crie um App
3. Adicione produto "Instagram"
4. Solicite permissões:
   - `instagram_basic`
   - `instagram_content_publish`
   - `instagram_manage_comments`
   - `instagram_manage_messages`
5. Gere Access Token de longa duração
6. Copie: Access Token e Instagram Account ID

**Importante**: Para DMs, você precisa de aprovação especial da Meta!

---

## 🎮 Modos de Execução

### Execução Única (Padrão)

```bash
OPERATION_MODE=once python -m app.main
```

Executa uma vez e para.

### Loop Contínuo

```bash
OPERATION_MODE=loop LOOP_INTERVAL_SECONDS=3600 python -m app.main
```

Executa a cada 1 hora (3600 segundos).

### Com Docker

```bash
# Edite o .env
OPERATION_MODE=loop
LOOP_INTERVAL_SECONDS=3600

# Execute
docker-compose up
```

---

## 🧪 Testar Sem APIs Reais

O sistema inclui **dados MOCK** para desenvolvimento:

1. **Shopee**: Retorna 3 ofertas fake automaticamente
2. **Instagram**: Configure credenciais reais (obrigatório)

Para testar apenas a lógica sem publicar:

```python
# Comente a linha de publicação em instagram_nodes.py
# client.publish_post(...)
```

---

## 📊 Verificar Logs

### Docker

```bash
# Logs em tempo real
docker-compose logs -f

# Últimas 100 linhas
docker-compose logs --tail=100
```

### Local

Logs são salvos em `logs/` (criado automaticamente).

```bash
tail -f logs/app.log
```

---

## ❗ Problemas Comuns

### Erro: "Shopee API credentials not configured"

**Solução**: Configure as credenciais no arquivo `.env`

---

### Erro: "Instagram Access Token expired"

**Solução**:
1. Gere um novo token de longa duração
2. Atualize no `.env`
3. Reinicie a aplicação

---

### Erro: "Cannot send DMs"

**Solução**:
- DMs requerem aprovação da Meta
- Verifique se tem a permissão `instagram_manage_messages`
- Solicite aprovação no Meta for Developers

---

### Docker: "Cannot connect to Docker daemon"

**Solução**:
1. Inicie o Docker Desktop
2. Verifique com `docker ps`

---

## 📚 Próximos Passos

Depois de rodar com sucesso:

1. ✅ Leia o [README.md](README.md) completo
2. ✅ Entenda a [ARCHITECTURE.md](ARCHITECTURE.md)
3. ✅ Customize filtros de ofertas no `.env`
4. ✅ Ajuste mensagens em `content_generator.py`
5. ✅ Configure monitoramento contínuo

---

## 🆘 Precisa de Ajuda?

- Consulte [README.md](README.md) para documentação completa
- Verifique [ARCHITECTURE.md](ARCHITECTURE.md) para detalhes técnicos
- Abra uma issue no repositório

---

**Boa sorte com seu projeto! 🚀**
