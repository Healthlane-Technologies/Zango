# App Secrets

App secrets store API keys, credentials, and other sensitive values encrypted in the database. They are scoped per app and decrypted at runtime.

## When to Use Secrets

**Always** store app-level credentials (API keys, tokens, passwords) as app secrets — **never** in the project `.env` file. The `.env` is for infrastructure config (DB, Redis, etc.), not application credentials.

```
✅ App secrets:  third-party API keys, webhook secrets, service passwords
✅ .env:         POSTGRES_*, REDIS_*, PLATFORM_USERNAME, FIELD_ENCRYPTION_KEY
❌ Never in .env: Stripe keys, SendGrid keys, any per-app credential
```

## Prerequisites

`FIELD_ENCRYPTION_KEY` must be set in `deploy/.env`. This is a 32-byte Fernet key used to encrypt all secret values at rest.

Generate one at bootstrap time:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add to `deploy/.env`:
```env
FIELD_ENCRYPTION_KEY=<generated-fernet-key>
```

**Never change this key after secrets have been created** — existing encrypted values will become unreadable.

---

## Key Naming Rules

Secret keys must match: `^[A-Z][a-z0-9_]*$`

- First character: uppercase letter
- Remaining characters: lowercase letters, digits, or `_`
- No spaces, no other special characters

```
✅ Valid:   My_api_key, Stripe_secret, Sendgrid_api_key, Vaxifast_api_id
❌ Invalid: MY_KEY, my_key, My-Key, My Key, _My_key
```

---

## Using Secrets in Code

```python
from zango.core.utils import get_app_secret

# Retrieve by key name
ACCESS_KEY_ID = get_app_secret("Vaxifast_api_id")
API_SECRET = get_app_secret("Stripe_secret")

# Retrieve by ID
value = get_app_secret(id=1)
```

`get_app_secret` raises `ValueError` if the key doesn't exist or the secret is inactive.

---

## Managing Secrets

Secrets are managed through the App Panel UI (App Settings → App Configuration → Secrets) or via the API. See [app-panel-api.md](../app-panel-api.md) → Secrets for full API reference.
