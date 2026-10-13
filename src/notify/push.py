"""Push via notifications.vertexdc.com. Config: env NOTIFICATIONS_SITE_KEY
(o NOTIFICATIONS_URL si cambia el host) o archivo data/push.json
{"site_key":...} — NUNCA commitear (ver .gitignore).
Sin credenciales: dry-run (loguea, no envia), igual que Telegram."""
import json
import os

import requests

URL = os.environ.get("NOTIFICATIONS_URL", "https://notifications.vertexdc.com")

def creds():
    key = os.environ.get("NOTIFICATIONS_SITE_KEY")
    if key:
        return key
    try:
        return json.load(open("data/push.json")).get("site_key")
    except FileNotFoundError:
        return None

def send_push(title: str, body: str, tag: str = "sismo", url: str = "/") -> dict:
    key = creds()
    if not key:
        print(f"[PUSH dry-run] {title} :: {body}", flush=True)
        return {"dry_run": True}
    # El gateway exige la llave dos veces: header `apikey` para enviar
    # y `site_key` en el cuerpo (doc oficial de integración).
    r = requests.post(f"{URL}/send_notification",
                      headers={"apikey": key},
                      json={"site_key": key, "title": title, "body": body,
                            "tag": tag, "url": url},
                      timeout=20)
    return {"ok": r.ok, "status": r.status_code}

def quake_push(ev: dict):
    return (f"Sismo M{ev.get('mag', '?')} — {ev.get('place', '?')}",
            f"Prof: {ev.get('depth', '?')} km · {ev.get('time', '')}")
