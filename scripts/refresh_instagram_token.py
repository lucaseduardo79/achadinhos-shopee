"""
Renova o token de longa duração do Instagram (Meta Graph API).

O token de longa duração (~60 dias) pode ser estendido chamando o endpoint
fb_exchange_token enquanto ainda estiver válido. Execute este script
periodicamente (ex: a cada 30 dias) para nunca deixar o token expirar.

Uso:
    python scripts/refresh_instagram_token.py
"""

import os
import re
import sys
import requests
from datetime import datetime, timezone
from pathlib import Path

ENV_FILE = Path(__file__).parent.parent / ".env"
API_VERSION = "v25.0"


def load_env() -> dict:
    env = {}
    with open(ENV_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env


def update_env_value(key: str, new_value: str):
    content = ENV_FILE.read_text(encoding="utf-8")
    pattern = rf"^({re.escape(key)}=).*$"
    updated = re.sub(pattern, rf"\g<1>{new_value}", content, flags=re.MULTILINE)
    ENV_FILE.write_text(updated, encoding="utf-8")


def exchange_token(current_token: str, app_id: str, app_secret: str) -> dict:
    resp = requests.get(
        f"https://graph.facebook.com/{API_VERSION}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": current_token,
        },
        timeout=15,
    )
    return resp.json()


def main():
    env = load_env()

    current_token = env.get("INSTAGRAM_ACCESS_TOKEN")
    app_id = env.get("META_EXCHANGE_APP_ID")
    app_secret = env.get("META_EXCHANGE_APP_SECRET")

    if not all([current_token, app_id, app_secret]):
        print("ERRO: Variáveis ausentes no .env (INSTAGRAM_ACCESS_TOKEN, META_EXCHANGE_APP_ID, META_EXCHANGE_APP_SECRET)")
        sys.exit(1)

    print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}] Renovando token...")

    result = exchange_token(current_token, app_id, app_secret)

    if "error" in result:
        print(f"ERRO: {result['error']['message']}")
        sys.exit(1)

    new_token = result["access_token"]
    expires_in = result.get("expires_in", 0)
    expires_days = expires_in // 86400

    update_env_value("INSTAGRAM_ACCESS_TOKEN", new_token)

    print(f"Token renovado com sucesso! Expira em ~{expires_days} dias.")
    print(f"Novo token: {new_token[:30]}...")


if __name__ == "__main__":
    main()
