# Security Policy

## Supported versions

Only the latest code on the `main` branch (currently version 1.2.0) gets security fixes. Older copies are not patched.

## Reporting a vulnerability

Private vulnerability reporting is not turned on for this repository yet.

To report a problem, open a GitHub issue with a title that starts with `[security]`. Describe the affected area and how serious it is, but **do not post exploit code or full reproduction steps in public.** A maintainer will contact you to get the details privately.

If a maintainer turns on private vulnerability reporting, use
https://github.com/MiMindMendinc/VoiceForge/security/advisories/new instead.

## Security model

VoiceForge is a local-first text-to-speech server. It is built for one trusted user on their own computer.

- **It listens on `127.0.0.1` by default** (`VOICEFORGE_HOST`), so only programs on the same computer can reach it.
- **It has no authentication.** Anyone who can reach the listening port can use every endpoint. This is intended for localhost use.
- Text you send is processed on your machine. The server does not send it anywhere.

## Built-in protections

All of these are in `server.py`.

- **Host header check.** Requests are accepted only when the Host header names `localhost`, `127.0.0.1` or `::1`, plus the bind address if it is a specific address. Other names get HTTP 400. This protects against DNS-rebinding attacks from web pages. Change the list with `VOICEFORGE_ALLOWED_HOSTS`. Setting it to `*` turns the check off.
- **Origin check.** If a request has an Origin header, it must match the server's own origin or one listed in `VOICEFORGE_ALLOWED_ORIGINS`. Otherwise it gets HTTP 403. Requests without an Origin header, such as from `curl` or scripts, are not affected.
- **No wildcard CORS.** CORS headers are sent only for the origins listed in `VOICEFORGE_ALLOWED_ORIGINS`, only for GET and POST, and only with the `Content-Type` header. The server refuses to start if that list contains `*`.
- **Request body limit.** HTTP request bodies are limited to 64 KiB (65,536 bytes). A larger `Content-Length` gets HTTP 413 before the body is read, and an invalid one gets HTTP 400. Bodies sent without a length (chunked) are counted as they arrive and stopped with HTTP 413 once they pass the limit. The spoken text itself is also limited to 5,000 characters.
- **Queue limit.** Speech is made one request at a time. At most `VOICEFORGE_MAX_QUEUE` speech requests (default 4, allowed range 1–1000) may run or wait at once. Requests beyond that get HTTP 503 with `Retry-After: 2`.
- **No stack traces in responses.** Errors come back as `{"error": "..."}`, and details go only to the server log.

These checks are not a replacement for authentication. There is no rate limiting beyond the queue limit, and no TLS. The server speaks plain HTTP.

## Do not expose it to untrusted networks

**Do not bind VoiceForge to `0.0.0.0`, `::`, or any other non-localhost address on a network you do not fully trust unless you add authentication in front of it,** for example a reverse proxy that requires a login and uses TLS. If you don't, anyone on that network can use the service and take up its capacity.

Setting `VOICEFORGE_ALLOWED_HOSTS` only changes which Host header values are accepted. It does **not** identify callers or restrict who they are.

## Scope

VoiceForge has not been certified or audited for any compliance, government, or military standard. Do not rely on it for that kind of assurance.
