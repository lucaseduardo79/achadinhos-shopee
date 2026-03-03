# 🛍️ Achadinhos Shopee - Automação Instagram

Sistema automatizado de curadoria de ofertas da Shopee e interação com usuários no Instagram, orquestrado com LangGraph.

## 📋 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Arquitetura](#arquitetura)
- [Funcionalidades](#funcionalidades)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Execução](#execução)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Fluxo do LangGraph](#fluxo-do-langgraph)
- [Desenvolvimento](#desenvolvimento)
- [Testes](#testes)
- [Roadmap](#roadmap)
- [Licença](#licença)

---

## 🎯 Sobre o Projeto

Este sistema automatiza todo o processo de:

1. **Curadoria de Ofertas**: Busca e seleciona automaticamente as melhores ofertas do dia da Shopee
2. **Publicação Automática**: Cria e publica posts no Instagram com as ofertas selecionadas
3. **Engajamento Inteligente**: Monitora comentários e interage automaticamente com usuários interessados
4. **Conversão**: Envia links de produtos via DM e responde publicamente aos comentários

Tudo orquestrado através de um **grafo LangGraph** que modela o fluxo completo de automação.

---

## 🏗️ Arquitetura

### Stack Tecnológico

- **Python 3.11+**: Linguagem principal
- **LangGraph**: Orquestração de agentes e fluxos
- **Meta Graph API**: Integração com Instagram
- **Shopee API**: Busca de ofertas e produtos
- **Docker**: Containerização e deployment
- **Requests**: HTTP client para APIs

### Diagrama de Fluxo

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUXO LANGGRAPH                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Buscar Ofertas] → [Selecionar Ofertas] →                 │
│                                                             │
│  → [Gerar Conteúdo] → [Publicar Post] →                    │
│                                                             │
│  → [Monitorar Comentários] → [Avaliar Comentário] ──┐      │
│         ↑                           │                │      │
│         │                           ↓                │      │
│         │                    [Enviar DM]             │      │
│         │                           │                │      │
│         │                           ↓                │      │
│         │                [Responder Comentário]      │      │
│         │                           │                │      │
│         └───────────────────────────┘                │      │
│                                                      │      │
│                                            [Sem mais │      │
│                                             comentários]    │
│                                                      │      │
│                                                      ↓      │
│                                              [Log Evento]   │
│                                                      │      │
│                                                      ↓      │
│                                                   [FIM]     │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Funcionalidades

### ✅ Implementadas

- [x] Busca automática de ofertas da Shopee
- [x] Filtragem por rating, desconto e comissão
- [x] Geração automática de legendas para Instagram
- [x] Publicação de posts com imagem
- [x] Monitoramento de comentários
- [x] Detecção de interesse em comentários
- [x] Envio automático de DMs com links
- [x] Resposta pública a comentários
- [x] Sistema de cooldown para evitar spam
- [x] Tratamento de erros e retry
- [x] Logging completo para auditoria
- [x] Execução via Docker

### 🚧 Roadmap (Ver seção completa)

- [ ] Banco de dados para persistência
- [ ] Dashboard de métricas
- [ ] Suporte a múltiplos posts por dia
- [ ] Sistema de agendamento

---

## 📦 Pré-requisitos

### Para Execução com Docker (Recomendado)

- Docker 20.10+
- Docker Compose 2.0+

### Para Execução Local

- Python 3.11+
- pip
- virtualenv (opcional, mas recomendado)

### Credenciais Necessárias

#### Shopee

1. Conta de afiliado na Shopee
2. API Key e API Secret (obter no painel de afiliados)
3. Partner ID

**Como obter**: [Shopee Open Platform](https://open.shopee.com/)

#### Instagram / Meta

1. Conta Instagram Business ou Creator
2. Página do Facebook vinculada
3. Access Token de longa duração (60 dias)
4. Instagram Account ID

**Como obter**:
1. Acesse [Meta for Developers](https://developers.facebook.com/)
2. Crie um app e solicite permissões para Instagram API
3. Gere um Access Token com as seguintes permissões:
   - `instagram_basic`
   - `instagram_content_publish`
   - `instagram_manage_comments`
   - `instagram_manage_messages` (para DMs)

---

## 🚀 Instalação

### Opção 1: Docker (Recomendado)

```bash
# Clone o repositório
git clone <seu-repo>
cd achadinhos_shopee

# Copie o arquivo de exemplo de variáveis de ambiente
cp .env.example .env

# Configure suas credenciais no arquivo .env
nano .env  # ou use seu editor preferido

# Execute o script de setup
chmod +x scripts/run_docker.sh
./scripts/run_docker.sh
```

### Opção 2: Ambiente Local

```bash
# Clone o repositório
git clone <seu-repo>
cd achadinhos_shopee

# Execute o script de setup
chmod +x scripts/dev_setup.sh
./scripts/dev_setup.sh

# O script irá:
# - Criar ambiente virtual
# - Instalar dependências
# - Criar arquivo .env

# Ative o ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Execute a aplicação
python -m app.main
```

---

## ⚙️ Configuração

### Arquivo .env

Configure todas as variáveis no arquivo `.env`:

```bash
# Modo de operação
OPERATION_MODE=once  # once, loop, ou scheduled

# Credenciais Shopee
SHOPEE_API_KEY=sua_api_key
SHOPEE_API_SECRET=seu_api_secret
SHOPEE_PARTNER_ID=seu_partner_id

# Credenciais Instagram
INSTAGRAM_ACCESS_TOKEN=seu_access_token
INSTAGRAM_ACCOUNT_ID=seu_account_id

# Filtros de ofertas
MIN_RATING=4.0
MIN_DISCOUNT=30.0
MIN_COMMISSION=5.0

# Configurações de comentários
COMMENT_COOLDOWN_MINUTES=60
```

### Parâmetros Importantes

| Parâmetro | Descrição | Valores | Padrão |
|-----------|-----------|---------|--------|
| `OPERATION_MODE` | Modo de execução | `once`, `loop`, `scheduled` | `once` |
| `LOOP_INTERVAL_SECONDS` | Intervalo entre execuções (modo loop) | Segundos | `3600` |
| `MIN_RATING` | Rating mínimo do produto | 0.0 - 5.0 | `4.0` |
| `MIN_DISCOUNT` | Desconto mínimo | Porcentagem | `30.0` |
| `MIN_COMMISSION` | Comissão mínima | Porcentagem | `5.0` |

---

## 🎮 Execução

### Com Docker

```bash
# Executar em foreground
docker-compose up

# Executar em background
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar
docker-compose down
```

### Local

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar
python -m app.main
```

### Modos de Operação

#### 1. Execução Única (`once`)

Executa o fluxo completo uma vez e finaliza.

```bash
OPERATION_MODE=once python -m app.main
```

#### 2. Loop Contínuo (`loop`)

Executa continuamente com intervalo configurável.

```bash
OPERATION_MODE=loop LOOP_INTERVAL_SECONDS=3600 python -m app.main
```

#### 3. Agendado (`scheduled`)

*(Em desenvolvimento)* Execução em horários específicos.

---

## 📁 Estrutura do Projeto

```
achadinhos_shopee/
│
├── app/                          # Código da aplicação
│   ├── graph/                    # LangGraph - Orquestração
│   │   ├── state.py              # Definição do estado do grafo
│   │   ├── graph.py              # Construção e execução do grafo
│   │   └── nodes/                # Nós do grafo
│   │       ├── shopee_nodes.py   # Nós de integração Shopee
│   │       ├── instagram_nodes.py # Nós de integração Instagram
│   │       └── observability_nodes.py # Nós de logging/observabilidade
│   │
│   ├── integrations/             # Integrações com APIs externas
│   │   ├── shopee/
│   │   │   └── client.py         # Cliente da API Shopee
│   │   └── instagram/
│   │       └── client.py         # Cliente da Meta Graph API
│   │
│   ├── services/                 # Serviços de negócio
│   │   ├── offer_selector.py    # Seleção e filtragem de ofertas
│   │   ├── content_generator.py # Geração de conteúdo para Instagram
│   │   └── comment_processor.py # Processamento de comentários
│   │
│   ├── utils/                    # Utilitários
│   │   └── logger.py             # Configuração de logging
│   │
│   └── main.py                   # Ponto de entrada da aplicação
│
├── docker/                       # Arquivos Docker
│   └── Dockerfile                # Definição da imagem Docker
│
├── scripts/                      # Scripts auxiliares
│   ├── dev_setup.sh              # Setup do ambiente de desenvolvimento
│   └── run_docker.sh             # Script para execução com Docker
│
├── tests/                        # Testes automatizados
│   └── test_offer_selector.py   # Testes do seletor de ofertas
│
├── .env.example                  # Exemplo de configuração
├── .gitignore                    # Arquivos ignorados pelo Git
├── docker-compose.yml            # Orquestração de containers
├── requirements.txt              # Dependências Python
└── README.md                     # Este arquivo
```

### Responsabilidades dos Módulos

#### `app/graph/` - Orquestração com LangGraph

- **`state.py`**: Define o estado tipado compartilhado entre nós
- **`graph.py`**: Constrói o grafo, define fluxos e condições
- **`nodes/`**: Implementa cada etapa do fluxo como nós independentes

#### `app/integrations/` - Integrações Externas

- **`shopee/client.py`**: API da Shopee (busca de produtos e ofertas)
- **`instagram/client.py`**: Meta Graph API (posts, comentários, DMs)

#### `app/services/` - Lógica de Negócio

- **`offer_selector.py`**: Filtra ofertas por rating, desconto, comissão
- **`content_generator.py`**: Cria legendas otimizadas para Instagram
- **`comment_processor.py`**: Valida comentários, detecta interesse, cooldown

---

## 🔄 Fluxo do LangGraph

### Nós Implementados

| Nó | Arquivo | Responsabilidade |
|----|---------|------------------|
| `fetch_offers` | `shopee_nodes.py` | Busca ofertas da Shopee |
| `select_offers` | `shopee_nodes.py` | Filtra e seleciona melhores ofertas |
| `generate_content` | `instagram_nodes.py` | Gera caption e prepara imagem |
| `publish_post` | `instagram_nodes.py` | Publica post no Instagram |
| `monitor_comments` | `instagram_nodes.py` | Busca comentários do post |
| `evaluate_comment` | `instagram_nodes.py` | Valida se comentário deve ser processado |
| `enviar_dm` | `instagram_nodes.py` | Envia DM com link do produto |
| `responder_comentario` | `instagram_nodes.py` | Responde comentário publicamente |
| `log_event` | `observability_nodes.py` | Registra eventos para auditoria |
| `handle_error` | `observability_nodes.py` | Trata erros e decide retry |

### Fluxos Condicionais

O grafo utiliza decisões condicionais para:

1. **Continuar monitoramento**: Se há comentários não processados
2. **Finalizar execução**: Quando não há mais comentários
3. **Tratamento de erro**: Retry automático até limite
4. **Cooldown de usuários**: Evita spam para o mesmo usuário

### Estado do Grafo

O estado (`GraphState`) é compartilhado entre todos os nós e contém:

- Ofertas (brutas e selecionadas)
- Conteúdo do post
- Lista de comentários
- Status de execução
- Metadados e IDs

---

## 🛠️ Desenvolvimento

### Configurar Ambiente de Dev

```bash
./scripts/dev_setup.sh
source venv/bin/activate
```

### Code Quality

```bash
# Formatação
black app/

# Linting
flake8 app/

# Type checking
mypy app/
```

### Adicionar Novos Nós ao Grafo

1. Crie a função do nó em `app/graph/nodes/`
2. Retorne um dicionário com atualizações do estado
3. Registre o nó em `app/graph/graph.py`:

```python
# Adiciona o nó
workflow.add_node("meu_novo_no", minha_funcao)

# Define conexões
workflow.add_edge("no_anterior", "meu_novo_no")
```

### Adicionar Nova Integração

1. Crie um novo cliente em `app/integrations/`
2. Implemente métodos para interagir com a API
3. Use o cliente nos nós do grafo

---

## 🧪 Testes

### Executar Testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=app

# Testes específicos
pytest tests/test_offer_selector.py
```

### Adicionar Novos Testes

Crie arquivos de teste em `tests/` seguindo o padrão:

```python
import pytest
from app.services.meu_servico import MeuServico

class TestMeuServico:
    def test_funcionalidade(self):
        servico = MeuServico()
        resultado = servico.fazer_algo()
        assert resultado == esperado
```

---

## 🗺️ Roadmap

### v1.0 (Atual)

- [x] Scaffold completo do projeto
- [x] Integração básica Shopee
- [x] Integração básica Instagram
- [x] Fluxo LangGraph funcional
- [x] Execução via Docker

### v1.1 (Próximo)

- [ ] Persistência em banco de dados (PostgreSQL)
- [ ] Cache com Redis
- [ ] Métricas e observabilidade (Prometheus)
- [ ] Dashboard web para monitoramento

### v2.0 (Futuro)

- [ ] Múltiplos posts por dia
- [ ] Suporte a múltiplas contas Instagram
- [ ] Sistema de agendamento avançado
- [ ] Machine learning para seleção de ofertas
- [ ] A/B testing de legendas
- [ ] Analytics de conversão

---

## 📝 Notas Importantes

### Limitações Conhecidas

1. **DMs no Instagram**: Requer aprovação especial da Meta. Verifique se tem as permissões necessárias.
2. **Rate Limits**: Tanto Shopee quanto Instagram têm limites de requisições. O sistema implementa cooldown básico.
3. **Shopee API**: A implementação atual usa dados MOCK. Configure a API real em produção.

### Boas Práticas

- **Tokens do Instagram**: Use tokens de longa duração (60 dias) e implemente refresh automático
- **Monitoramento**: Acompanhe os logs em `logs/` para identificar problemas
- **Backup**: Faça backup regular do arquivo `.env` (mas não versione no Git!)

---

## 📄 Licença

Este projeto é fornecido como exemplo educacional. Adapte conforme necessário para seu uso.

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

---

## 📧 Contato

Para dúvidas ou sugestões, abra uma issue no repositório.

---

**Desenvolvido com ❤️ usando LangGraph e Python**
