"""
The single notification seam. Hooks call notify(); nothing else sends mail/SMS.

Until a provider is wired (the Zango `communication` package, SMTP, an SMS
gateway), notify() logs the message and records it so tests can assert it was
sent. Wiring a provider means changing send_via_provider() only.
"""

import logging

logger = logging.getLogger("zas.notify")

SENT = []  # last messages, newest last (tests read this in-process; capped)


def send_via_provider(channel, to, subject, body, **extra):
    """Replace this body to deliver for real. Return True when handed off."""
    return False


def notify(event, to, subject="", body="", channel="email", **extra):
    """Send one message. `event` is a stable key (e.g. "vendor.approved") for tests and logs."""
    msg = {"event": event, "channel": channel, "to": to, "subject": subject, "body": body, **extra}
    delivered = False
    try:
        delivered = bool(send_via_provider(channel, to, subject, body, **extra))
    except Exception:
        logger.exception("zas.notify: provider failed for %s", event)
    msg["delivered"] = delivered
    logger.info("zas.notify %s → %s (%s)%s", event, to, channel, "" if delivered else " [not delivered: no provider]")
    SENT.append(msg)
    del SENT[:-200]
    _outbox(msg)
    return msg


def _outbox(msg):
    """DEBUG only: append to <ws>/.zas/outbox.jsonl so scenario tests (another process) can assert
    that a message went out. Never in production, and never fails the caller."""
    try:
        import json
        import os
        from django.conf import settings
        if not getattr(settings, "DEBUG", False):
            return
        ws = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        os.makedirs(os.path.join(ws, ".zas"), exist_ok=True)
        import time
        with open(os.path.join(ws, ".zas", "outbox.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({**msg, "at": time.time()}, default=str) + "\n")
    except Exception:
        logger.debug("zas.notify: outbox write skipped", exc_info=True)
