"""Push via vertexdc: payload exacto y dry-run sin llave (sin red)."""
from unittest.mock import patch

from src.notify import push as P


def test_send_push_payload(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOTIFICATIONS_SITE_KEY", "psk_test")
    with patch.object(P.requests, "post") as post:
        post.return_value.ok = True
        post.return_value.status_code = 200
        r = P.send_push("M5.1 — Azuero", "Prof: 10 km", tag="sismo-m5")
    assert r == {"ok": True, "status": 200}
    url, kw = post.call_args.args[0], post.call_args.kwargs
    assert url == "https://notifications.vertexdc.com/send_notification"
    assert kw["json"] == {"site_key": "psk_test", "title": "M5.1 — Azuero",
                         "body": "Prof: 10 km", "tag": "sismo-m5"}


def test_send_push_dry_run_sin_llave(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("NOTIFICATIONS_SITE_KEY", raising=False)
    with patch.object(P.requests, "post") as post:
        r = P.send_push("t", "b")
    assert r == {"dry_run": True}
    post.assert_not_called()


def test_quake_push_texto_plano():
    t, b = P.quake_push({"mag": 5.1, "place": "Azuero", "depth": 10,
                         "time": "2026-10-13 01:00"})
    assert t == "Sismo M5.1 — Azuero" and "<" not in t + b
