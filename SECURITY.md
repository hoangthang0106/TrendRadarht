# Security - TrendRadarht

## Secrets

Never commit Telegram tokens, webhook URLs, passwords, API keys, or S3 keys.

This repository keeps only `docker/.env.example`. Real `.env` files, secret directories, private keys, and runtime output are excluded by `.gitignore`.

For Portainer, store these under **Stack -> Environment variables**:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

For stronger isolation, the application also supports file-backed values:

- `TELEGRAM_BOT_TOKEN_FILE`
- `TELEGRAM_CHAT_ID_FILE`

The container diagnostic command masks token/key/password/chat ID values as `***SET***`.

If a Telegram bot token is exposed, revoke it in BotFather, replace it in Portainer, and redeploy.

## Web report

Port 8080 binds to `127.0.0.1` by default. The report server disables directory listing and blocks database, TXT, config, environment, and key files.

For LAN access, bind to the Ubuntu LAN address and restrict TCP/8080 with the host firewall. Do not forward port 8080 directly to the Internet.

## Container versions

The customized stack pins the main runtime components instead of using `:latest`:

- NewsNow `v0.0.42`
- Ollama `0.40.4`
- uv `0.13.1`

The TrendRadar container also runs with `no-new-privileges`.
