"""Shared helpers for the honey-encryption evaluation scripts.

Nothing cryptographic is reimplemented here. `reproducible_secrets` only
temporarily swaps `honey.secrets` for a seeded shim so `honey.encrypt` becomes
reproducible without touching honey.py.
"""
from __future__ import annotations

import contextlib
import random
import secrets
import subprocess


def collect_git_info(timeout: float = 5.0) -> dict:
    """Best-effort git metadata; never raises."""

    def _run(*args: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", *args],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    commit = _run("rev-parse", "HEAD")
    if not commit:
        return {"available": False}
    dirty = _run("status", "--porcelain")
    return {
        "available": True,
        "commit": commit,
        "short_commit": _run("rev-parse", "--short", "HEAD"),
        "branch": _run("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(dirty) if dirty is not None else None,
    }


class _SecretsShim:
    """Minimal stand-in for the secrets module, backed by a seeded RNG."""

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng

    def randbelow(self, n: int) -> int:
        return self._rng.randrange(n)

    def token_bytes(self, n: int) -> bytes:
        return self._rng.randbytes(n)

    def token_hex(self, n: int) -> str:
        return self._rng.randbytes(n).hex()

    def choice(self, seq):
        return self._rng.choice(seq)


@contextlib.contextmanager
def reproducible_secrets(rng: random.Random | None):
    """Temporarily route `honey.secrets` through `rng` when `rng` is not None."""
    if rng is None:
        yield
        return
    import honey  # local import avoids a cycle at module load
    original = honey.secrets
    honey.secrets = _SecretsShim(rng)
    try:
        yield
    finally:
        honey.secrets = original


def seeded_rng(seed: int | None) -> random.Random | None:
    return None if seed is None else random.Random(seed)


def random_bytes(rng: random.Random | None, n: int) -> bytes:
    return secrets.token_bytes(n) if rng is None else rng.randbytes(n)


def random_hex(rng: random.Random | None, n: int) -> str:
    return secrets.token_hex(n) if rng is None else rng.randbytes(n).hex()