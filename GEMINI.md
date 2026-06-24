# 🛡️ SARVA Firewall Security Mandates

## 🛡️ Authentication & Authorization
- **JWT Mandatory:** All backend endpoints (except `/api/auth/login` and `/api/health`) MUST be protected with the `@token_required` decorator from `utils.security`.
- **Frontend Headers:** Use the `secureFetch` wrapper in `src/lib/api.ts` for all API calls to ensure the `Authorization` header is included.
- **Passwords:** NEVER store plaintext passwords. Use `hash_password` and `verify_password` utilities.

## 🚀 Injection Prevention
- **OS Commands:** Use list-based arguments with `subprocess.run`. NEVER use `shell=True` or string concatenation for shell commands.
- **File Paths:** Always use `is_safe_path` in `backend/routes/advanced_analysis.py` or similar logic to prevent Path Traversal/LFI.
- **Input Sanitization:** Maintain and extend the WAF rules in `backend/app.py`.

## 📦 Secrets Management
- **Environment Variables:** All sensitive keys (JWT secrets, API keys) MUST be stored in `.env` and accessed via `os.getenv`.
- **Hardcoding:** NEVER hardcode secrets in the codebase or documentation.

## 🌐 Network Security
- **CORS:** Restrict `CORS_ORIGINS` to trusted domains in production.
- **Security Headers:** All responses must include CSP, HSTS, X-Content-Type-Options, etc., as configured in `backend/app.py`.
- **Rate Limiting:** Use the `limiter` instance in `backend/app.py` for sensitive endpoints.
