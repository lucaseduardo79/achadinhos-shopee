# 🏗️ Arquitetura do Sistema - LangGraph

Este documento explica em detalhes como o sistema é arquitetado usando LangGraph.

## 📊 Visão Geral do LangGraph

LangGraph é uma biblioteca para construir aplicações stateful e multi-agente usando grafos. Cada nó do grafo representa uma operação, e as arestas definem o fluxo de execução.

### Vantagens do LangGraph

1. **Estado Explícito**: Todo o estado é tipado e compartilhado
2. **Fluxo Visual**: O grafo pode ser visualizado e entendido facilmente
3. **Modularidade**: Cada nó é independente e testável
4. **Condições**: Suporte nativo a fluxos condicionais
5. **Retry**: Tratamento de erros e retry integrado

---

## 🔄 Grafo Completo

```
                    ┌─────────────────┐
                    │  INÍCIO (init)  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Buscar Ofertas  │
                    │   (Shopee API)  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │Selecionar Ofertas│
                    │  (Filtros apply) │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Gerar Conteúdo  │
                    │   (Caption +    │
                    │    Imagem)      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Publicar Post   │
                    │  (Instagram)    │
                    └────────┬────────┘
                             │
                             ▼
        ┌───────────────────────────────────────┐
        │                                       │
        │      LOOP DE MONITORAMENTO            │
        │                                       │
        │    ┌─────────────────────┐            │
        │    │ Monitorar           │            │
        │    │ Comentários         │            │
        │    └──────────┬──────────┘            │
        │               │                       │
        │               ▼                       │
        │    ┌─────────────────────┐            │
        │    │   Avaliar           │            │
        │    │   Comentário        │            │
        │    └──────────┬──────────┘            │
        │               │                       │
        │          ┌────┴────┐                  │
        │          │         │                  │
        │     [Processar?]  [Não processar]     │
        │          │         │                  │
        │        SIM        NÃO                 │
        │          │         │                  │
        │          ▼         ▼                  │
        │    ┌─────────┐  [Próximo]            │
        │    │Enviar DM│    comentário         │
        │    └────┬────┘      │                │
        │         │           │                │
        │         ▼           │                │
        │    ┌─────────┐      │                │
        │    │Responder│      │                │
        │    │Comentário     │                │
        │    └────┬────┘      │                │
        │         │           │                │
        │         └───────┬───┘                │
        │                 │                    │
        │                 ▼                    │
        │          [Há mais comentários?]      │
        │                 │                    │
        │          ┌──────┴──────┐             │
        │         SIM            NÃO           │
        │          │              │            │
        │          └──────┐       │            │
        │                 │       │            │
        └─────────────────┘       │
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  Log Evento     │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │      FIM        │
                         └─────────────────┘

        [Em caso de erro, vai para handle_error]
                         ┌─────────────────┐
                         │  Handle Error   │
                         │  (Max 3 retry)  │
                         └────────┬────────┘
                                  │
                         ┌────────┴────────┐
                        SIM               NÃO
                    [Retry < 3]      [Retry >= 3]
                         │                 │
                         ▼                 ▼
                  [Volta início]     [Finaliza com erro]
```

---

## 📦 Estado do Grafo (`GraphState`)

O estado é o coração do sistema. Ele é passado entre todos os nós e contém todas as informações necessárias.

### Estrutura do Estado

```python
class GraphState(TypedDict):
    # Ofertas da Shopee
    raw_offers: Optional[List[Dict[str, Any]]]      # Ofertas brutas da API
    selected_offers: Optional[List[ProductOffer]]   # Ofertas filtradas
    current_offer: Optional[ProductOffer]           # Oferta sendo processada

    # Conteúdo do Instagram
    post_content: Optional[InstagramPost]           # Post gerado

    # Comentários e interações
    comments: Optional[List[Comment]]               # Todos os comentários
    current_comment: Optional[Comment]              # Comentário sendo processado

    # Status e controle de fluxo
    step: str                                       # Etapa atual
    error: Optional[str]                            # Erro, se houver
    retry_count: int                                # Contagem de retries

    # Metadados
    execution_id: str                               # ID único da execução
    started_at: datetime                            # Timestamp de início
    metadata: Optional[Dict[str, Any]]              # Dados adicionais
```

### Fluxo do Estado

```
Início:
  step: "init"
  raw_offers: None
  selected_offers: None
  ...

Após buscar ofertas:
  step: "offers_fetched"
  raw_offers: [offer1, offer2, ...]
  ...

Após selecionar:
  step: "offers_selected"
  selected_offers: [best_offer]
  current_offer: best_offer
  ...

Após publicar:
  step: "post_published"
  post_content: {post_id: "123", ...}
  ...
```

---

## 🔧 Nós do Grafo

### 1. Buscar Ofertas (`buscar_ofertas_shopee`)

**Responsabilidade**: Buscar ofertas do dia na Shopee

**Entrada**:
- Estado inicial do grafo

**Saída**:
```python
{
    "raw_offers": [...],
    "step": "offers_fetched",
    "error": None
}
```

**Tratamento de Erro**:
```python
{
    "step": "error",
    "error": "Erro ao buscar ofertas: ..."
}
```

---

### 2. Selecionar Ofertas (`selecionar_ofertas_do_dia`)

**Responsabilidade**: Filtrar ofertas por critérios (rating, desconto, comissão)

**Critérios de Filtro**:
- Rating >= 4.0 (configurável)
- Desconto >= 30% (configurável)
- Comissão >= 5% (configurável)
- Categorias permitidas (opcional)

**Entrada**:
- `state["raw_offers"]`

**Saída**:
```python
{
    "selected_offers": [best_offer],
    "current_offer": best_offer,
    "step": "offers_selected",
    "error": None
}
```

---

### 3. Gerar Conteúdo (`gerar_conteudo_instagram`)

**Responsabilidade**: Criar caption otimizada e preparar imagem

**Entrada**:
- `state["current_offer"]`

**Lógica**:
1. Seleciona emoji baseado na categoria
2. Cria título chamativo
3. Adiciona informações de preço e desconto
4. Insere call-to-action
5. Adiciona hashtags relevantes

**Saída**:
```python
{
    "post_content": {
        "image_url": "...",
        "caption": "🎁 ACHADO DO DIA! ...",
        "product_link": "..."
    },
    "step": "content_generated"
}
```

---

### 4. Publicar Post (`publicar_post`)

**Responsabilidade**: Publicar no Instagram via Meta Graph API

**Entrada**:
- `state["post_content"]`

**Processo**:
1. Cria container de mídia
2. Aguarda processamento
3. Publica post

**Saída**:
```python
{
    "post_content": {
        ...,
        "post_id": "instagram_post_id"
    },
    "step": "post_published"
}
```

---

### 5. Monitorar Comentários (`monitorar_comentarios`)

**Responsabilidade**: Buscar comentários do post publicado

**Entrada**:
- `state["post_content"]["post_id"]`

**Saída**:
```python
{
    "comments": [
        {
            "comment_id": "...",
            "user_id": "...",
            "username": "...",
            "text": "quero o link",
            "processed": False
        },
        ...
    ],
    "step": "comments_monitored"
}
```

---

### 6. Avaliar Comentário (`avaliar_comentario`)

**Responsabilidade**: Determinar se comentário deve ser processado

**Critérios de Avaliação**:
1. ✅ Não foi processado antes
2. ✅ Usuário não está em cooldown (60 min default)
3. ✅ Contém palavras-chave de interesse
4. ✅ Não é spam

**Palavras-chave de Interesse**:
- "link", "quero", "preço", "comprar", "quanto", etc.

**Saída (Deve processar)**:
```python
{
    "current_comment": comment,
    "step": "comment_evaluated"
}
```

**Saída (Sem comentários novos)**:
```python
{
    "current_comment": None,
    "step": "no_comments_to_process"
}
```

---

### 7. Enviar DM (`enviar_dm_com_link`)

**Responsabilidade**: Enviar mensagem privada com link do produto

**Entrada**:
- `state["current_comment"]`
- `state["current_offer"]`

**Mensagem Enviada**:
```
Oi! 👋 Vi seu comentário e já te mandei o link do produto com desconto.

🔗 Link: [URL do produto]

Qualquer dúvida é só me chamar!
```

**Saída**:
```python
{
    "step": "dm_sent"
}
```

---

### 8. Responder Comentário (`responder_comentario_publico`)

**Responsabilidade**: Responder publicamente ao comentário

**Resposta Padrão**:
```
Te enviamos o link do produto por DM 😉
```

**Saída**:
```python
{
    "current_comment": {
        ...,
        "processed": True  # Marca como processado
    },
    "step": "comment_replied"
}
```

---

## 🔀 Fluxos Condicionais

### 1. Continuação do Monitoramento

**Função**: `should_continue_monitoring(state)`

```python
if state["step"] == "comment_evaluated" and state["current_comment"]:
    return "enviar_dm"  # Há comentário para processar

if state["step"] == "no_comments_to_process":
    return "end"  # Finaliza execução

if state["step"] == "error":
    return "handle_error"  # Trata erro
```

---

### 2. Retry em Caso de Erro

**Função**: `should_retry(state)`

```python
if state["step"] == "retry" and state["retry_count"] < 3:
    return "fetch_offers"  # Tenta novamente do início

if state["retry_count"] >= 3:
    return "end"  # Desiste após 3 tentativas
```

---

## 🎯 Cenários de Uso

### Cenário 1: Execução Bem-Sucedida Completa

```
1. Busca 50 ofertas da Shopee
2. Filtra para 1 oferta (melhor rating/desconto)
3. Gera caption otimizada
4. Publica post no Instagram
5. Aguarda 5 minutos
6. Monitora comentários
7. Encontra 3 comentários interessados
8. Para cada comentário:
   - Envia DM com link
   - Responde publicamente
   - Marca como processado
9. Finaliza com sucesso
```

---

### Cenário 2: Erro ao Buscar Ofertas

```
1. Tenta buscar ofertas
2. Shopee API retorna erro 500
3. Vai para handle_error
4. retry_count = 1 < 3
5. Volta para buscar_ofertas
6. Tenta novamente
7. Sucesso na 2ª tentativa
8. Continua fluxo normal
```

---

### Cenário 3: Nenhum Comentário Novo

```
1. ... (publica post)
2. Monitora comentários
3. Todos já foram processados
4. Avaliar comentário retorna "no_comments_to_process"
5. Vai direto para log_event
6. Finaliza
```

---

## 🛡️ Tratamento de Erros

### Estratégia de Retry

- **Máximo de tentativas**: 3
- **Ponto de retry**: Recomeça do início (buscar_ofertas)
- **Persistência do estado**: Mantém execution_id e metadados

### Errors Tratados

1. **Erro de API Externa**: Retry automático
2. **Ofertas insuficientes**: Finaliza sem erro
3. **Post já publicado**: Continua para monitoramento
4. **Comentário já processado**: Ignora e próximo

---

## 📈 Extensibilidade

### Como Adicionar um Novo Nó

**Exemplo**: Adicionar nó para enviar email de resumo

```python
# 1. Criar função do nó
def enviar_email_resumo(state: GraphState) -> Dict[str, Any]:
    execution_id = state["execution_id"]
    offer = state["current_offer"]

    # Lógica de envio de email
    send_email(
        to="admin@exemplo.com",
        subject=f"Resumo da execução {execution_id}",
        body=f"Oferta publicada: {offer['name']}"
    )

    return {
        "step": "email_sent",
        "error": None
    }

# 2. Adicionar ao grafo
workflow.add_node("enviar_email", enviar_email_resumo)

# 3. Conectar no fluxo
workflow.add_edge("log_event", "enviar_email")
workflow.add_edge("enviar_email", END)
```

---

### Como Adicionar Estado Customizado

```python
# 1. Estender GraphState
class ExtendedGraphState(GraphState):
    email_sent: bool
    sms_sent: bool
    custom_metadata: Dict[str, Any]

# 2. Usar no grafo
workflow = StateGraph(ExtendedGraphState)
```

---

## 🔍 Debugging e Observabilidade

### Logging em Cada Nó

Todos os nós fazem log detalhado:

```python
logger.info(f"[{execution_id}] Buscando ofertas da Shopee...")
logger.info(f"[{execution_id}] {len(offers)} ofertas encontradas")
```

### Rastreamento de Execução

Cada execução tem um `execution_id` único:

```
exec_20260105_143022
```

Permite rastrear toda a execução nos logs.

---

## 🎓 Conceitos Importantes do LangGraph

### 1. Estado Imutável

Nós **não modificam** o estado diretamente. Eles retornam um **dicionário de atualizações** que é mesclado ao estado.

```python
# ❌ ERRADO
def meu_no(state: GraphState):
    state["step"] = "novo_step"  # Não faça isso!

# ✅ CORRETO
def meu_no(state: GraphState) -> Dict[str, Any]:
    return {"step": "novo_step"}
```

---

### 2. Arestas Condicionais

Permitem decisões dinâmicas no fluxo:

```python
workflow.add_conditional_edges(
    "avaliar_comentario",  # Nó de origem
    funcao_de_decisao,     # Função que retorna string
    {
        "processar": "enviar_dm",    # Mapeamento
        "ignorar": "log_event"
    }
)
```

---

### 3. Compilação do Grafo

Antes de executar, o grafo é **compilado**:

```python
app = workflow.compile()
```

Isso valida:
- Todos os nós estão conectados
- Não há ciclos infinitos (exceto loops intencionais)
- Tipos de estado são compatíveis

---

## 📚 Recursos Adicionais

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Documentation](https://python.langchain.com/)
- [Meta Graph API](https://developers.facebook.com/docs/graph-api)
- [Shopee Open Platform](https://open.shopee.com/)

---

**Este documento é uma referência viva. Atualize conforme o sistema evolui!**
