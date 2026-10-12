"""Alertas RT por Telegram. Config: env TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID,
o archivo data/telegram.json {"token":..., "chat_id":...}.
Sin credenciales: dry-run (loguea, no envia)."""
import json
import os

import requests

API = "https://api.telegram.org/bot{token}/sendMessage"

def creds():
    tok = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if tok and chat:
        return tok, chat
    try:
        c = json.load(open("data/telegram.json"))
        return c.get("token"), c.get("chat_id")
    except FileNotFoundError:
        return None, None

def send(text: str) -> dict:
    tok, chat = creds()
    if not tok or not chat:
        print(f"[ALERTA dry-run] {text}", flush=True)
        return {"dry_run": True}
    r = requests.post(API.format(token=tok), json={"chat_id": chat, "text": text,
                                                   "parse_mode": "HTML"}, timeout=20)
    return {"ok": r.ok, "status": r.status_code}

def quake_text(ev: dict, extra: str = "") -> str:
    return (f"🚨 <b>M{ev.get('mag', '?')} — {ev.get('place', '?')}</b>\n"
            f"Prof: {ev.get('depth', '?')} km · {ev.get('time', '')}\n{extra}")
