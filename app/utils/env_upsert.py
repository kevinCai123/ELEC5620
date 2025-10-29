from pathlib import Path
from typing import Dict

ENV_PATH = Path(".env")


def upsert_env_vars(pairs: Dict[str, str]) -> None:
    """Idempotently upsert key=value pairs into .env while preserving other lines."""
    if not ENV_PATH.exists():
        ENV_PATH.write_text("", encoding="utf-8")
        try:
            ENV_PATH.chmod(0o600)
        except Exception:
            pass

    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    kv = {}
    order = []

    # Parse existing lines
    for ln in lines:
        if not ln.strip() or ln.strip().startswith("#") or "=" not in ln:
            order.append(ln)
            continue
        k, v = ln.split("=", 1)
        kv[k.strip()] = v
        order.append(k.strip())

    # Upsert incoming
    for k, v in pairs.items():
        kv[k] = v
        if k not in order:
            order.append(k)

    # Rebuild file preserving comments/blank lines in-place where possible:
    out = []
    seen_keys = set()
    for ln in lines:
        if not ln.strip() or ln.strip().startswith("#") or "=" not in ln:
            out.append(ln)
            continue
        k = ln.split("=", 1)[0].strip()
        if k in kv and k not in seen_keys:
            out.append(f"{k}={kv[k]}")
            seen_keys.add(k)

    # Append any new keys not previously present
    for k in order:
        if k in kv and k not in seen_keys:
            out.append(f"{k}={kv[k]}")
            seen_keys.add(k)

    ENV_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
