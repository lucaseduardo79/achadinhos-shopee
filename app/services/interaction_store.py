"""
Armazena interações de usuários (comentários + links enviados) em DuckDB.

Tabela `interactions`:
  - username    : nome do usuário que comentou
  - product_link: link de afiliado enviado por DM
  - comment_id  : ID do comentário (chave única, evita duplicatas)
  - user_id     : ID do usuário no Instagram
  - product_name: nome do produto (opcional)
  - post_id     : ID do post onde o comentário foi feito
  - interacted_at: quando a interação foi registrada
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

import duckdb

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "data" / "interactions.duckdb"

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS interactions (
    id           INTEGER PRIMARY KEY,
    comment_id   VARCHAR UNIQUE NOT NULL,
    user_id      VARCHAR,
    username     VARCHAR NOT NULL,
    product_link VARCHAR NOT NULL,
    product_name VARCHAR,
    post_id      VARCHAR,
    interacted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

_SEQUENCE_SQL = "CREATE SEQUENCE IF NOT EXISTS interactions_id_seq START 1"


def _connect() -> duckdb.DuckDBPyConnection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = duckdb.connect(str(DB_PATH))
    conn.execute(_SEQUENCE_SQL)
    conn.execute(_CREATE_TABLE_SQL)
    return conn


def save_interaction(
    comment_id: str,
    username: str,
    product_link: str,
    user_id: str = "",
    product_name: str = "",
    post_id: str = "",
) -> bool:
    """
    Salva a interação de um usuário.

    Returns:
        True se inserido, False se o comment_id já existia.
    """
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO interactions (id, comment_id, user_id, username, product_link, product_name, post_id, interacted_at)
            VALUES (nextval('interactions_id_seq'), ?, ?, ?, ?, ?, ?, ?)
            """,
            [comment_id, user_id, username, product_link, product_name, post_id, datetime.now()],
        )
        conn.commit()
        logger.info(f"Interação salva: @{username} → {product_link}")
        return True
    except duckdb.ConstraintException:
        logger.debug(f"Interação já registrada para comment_id={comment_id}")
        return False
    finally:
        conn.close()


def get_interactions(limit: int = 100) -> list[dict]:
    """
    Retorna as interações mais recentes.

    Args:
        limit: Número máximo de registros retornados.

    Returns:
        Lista de dicts com campos da tabela.
    """
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT comment_id, username, product_link, product_name, post_id, interacted_at "
            "FROM interactions ORDER BY interacted_at DESC LIMIT ?",
            [limit],
        ).fetchall()
        cols = ["comment_id", "username", "product_link", "product_name", "post_id", "interacted_at"]
        return [dict(zip(cols, row)) for row in rows]
    finally:
        conn.close()


def get_user_interactions(username: str) -> list[dict]:
    """
    Retorna todas as interações de um usuário específico.
    """
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT comment_id, username, product_link, product_name, post_id, interacted_at "
            "FROM interactions WHERE username = ? ORDER BY interacted_at DESC",
            [username],
        ).fetchall()
        cols = ["comment_id", "username", "product_link", "product_name", "post_id", "interacted_at"]
        return [dict(zip(cols, row)) for row in rows]
    finally:
        conn.close()


def count_interactions() -> int:
    """Retorna o total de interações registradas."""
    conn = _connect()
    try:
        return conn.execute("SELECT COUNT(*) FROM interactions").fetchone()[0]
    finally:
        conn.close()
