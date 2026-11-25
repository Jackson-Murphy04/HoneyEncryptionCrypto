"""Pooled wrong-password experiment across many independent ciphertexts.

For each of N ciphertexts (independent random message and random correct
password), G distinct random wrong-password guesses are tried through the
prototype's real PBKDF2/XOR/decode path. Results are pooled for a global
chi-square and TVD; per-ciphertext dispersion and per-message outlier
diagnostics are reported alongside.

- Pooled statistics (chi-square, p-value, TVD, TVD bootstrap CI) use all N*G
  guesses.
- Per-ciphertext dispersion reports the distribution of per-ciphertext TVD and
  of the number of distinct decoded messages, so you can see how much each
  ciphertext varies.
- Outliers lists the top messages by contribution to the pooled chi-square and
  every message whose pooled standardized residual exceeds 2, 3, or the
  Bonferroni-corrected threshold.

Not a proof of honey-encryption security: every wrong guess still returns an
in-domain sentence, and the message model has only 112 entries.

Usage:
    python pooled_wrong_password.py --seed 12345
    python pooled_wrong_password.py --ciphertexts 10 --guesses-per-ciphertext 50 --seed 1
"""
from __future__ import annotations

import argparse
import json
import secrets
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import chi2 as chi2_dist
from scipy.stats import norm

import honey
from _eval_helpers import (
    collect_git_info,
    random_hex,
    reproducible_secrets,
    seeded_rng,
)


DEFAULT_CIPHERTEXTS = 40
DEFAULT_GUESSES = 100
DEFAULT_BOOTSTRAP = 2000
DEFAULT_CI_LEVEL = 0.95
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parent
    / "evaluation_results"
    / "pooled_wrong_password_results.json"
)
MESSAGE_INDEX = {m: i for i, m in enumerate(honey.MESSAGES)}
MESSAGE_COUNT = honey.MESSAGE_COUNT


def _quantiles(values: np.ndarray) -> dict:
    return {
        "min": float(np.min(values)),
        "q1": float(np.quantile(values, 0.25)),
        "median": float(np.median(values)),
        "q3": float(np.quantile(values, 0.75)),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
        "std": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
        "values": [float(v) for v in values],
    }


def _quantiles_int(values: np.ndarray) -> dict:
    return {
        "min": int(np.min(values)),
        "q1": float(np.quantile(values, 0.25)),
        "median": float(np.median(values)),
        "q3": float(np.quantile(values, 0.75)),
        "max": int(np.max(values)),
        "mean": float(np.mean(values)),
        "std": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
        "values": [int(v) for v in values],
    }


def run(
    n_ciphertexts: int,
    guesses: int,
    seed: int | None,
    output: Path,
    ci_level: float,
    n_boot: int,
) -> dict:
    if n_ciphertexts < 1:
        raise ValueError("ciphertexts must be >= 1")
    if guesses < 1:
        raise ValueError("guesses per ciphertext must be >= 1")

    output.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()

    rng = seeded_rng(seed)
    boot_rng = np.random.default_rng(seed) if seed is not None else np.random.default_rng()

    per_ct_counts: list[np.ndarray] = []
    per_ct_tvds: list[float] = []
    per_ct_distinct: list[int] = []
    pooled = np.zeros(MESSAGE_COUNT, dtype=np.int64)

    for _ in range(n_ciphertexts):
        if rng is None:
            message = secrets.choice(honey.MESSAGES)
            correct_password = "correct-" + secrets.token_hex(16)
        else:
            message = honey.MESSAGES[rng.randrange(MESSAGE_COUNT)]
            correct_password = "correct-" + rng.randbytes(16).hex()

        with reproducible_secrets(rng):
            record = honey.encrypt(message, correct_password)
        record.pop("example", None)

        seen: set[str] = set()
        counts = np.zeros(MESSAGE_COUNT, dtype=np.int64)
        while len(seen) < guesses:
            candidate = "wrong-" + random_hex(rng, 16)
            if candidate == correct_password or candidate in seen:
                continue
            seen.add(candidate)
            decoded = honey.decrypt(record, candidate)
            counts[MESSAGE_INDEX[decoded]] += 1

        per_ct_counts.append(counts)
        pooled += counts

        p = counts / guesses
        per_ct_tvds.append(float(0.5 * np.abs(p - 1.0 / MESSAGE_COUNT).sum()))
        per_ct_distinct.append(int((counts > 0).sum()))

    trials = n_ciphertexts * guesses
    uniform = 1.0 / MESSAGE_COUNT
    expected = trials / MESSAGE_COUNT

    # Pooled goodness-of-fit vs uniform.
    chi2_stat = float(((pooled - expected) ** 2 / expected).sum())
    p_value = float(chi2_dist.sf(chi2_stat, MESSAGE_COUNT - 1))
    tvd = float(0.5 * np.abs(pooled / trials - uniform).sum())

    # Cluster bootstrap over ciphertexts (within-ciphertext dependence).
    stack = np.stack(per_ct_counts)  # shape (n_ciphertexts, MESSAGE_COUNT)
    boot_tvds = np.empty(n_boot, dtype=np.float64)
    for b in range(n_boot):
        idx = boot_rng.integers(0, n_ciphertexts, size=n_ciphertexts)
        boot_pooled = stack[idx].sum(axis=0)
        boot_tvds[b] = 0.5 * np.abs(boot_pooled / trials - uniform).sum()
    alpha = 1.0 - ci_level
    tvd_ci_lo = float(np.quantile(boot_tvds, alpha / 2))
    tvd_ci_hi = float(np.quantile(boot_tvds, 1 - alpha / 2))

    # Per-message residual / contribution diagnostics.
    z_scores = (pooled - expected) / np.sqrt(expected)
    contributions = z_scores ** 2
    bonferroni_z = float(norm.ppf(1 - alpha / (2 * MESSAGE_COUNT)))

    def _row(i: int) -> dict:
        return {
            "message_index": int(i),
            "message": honey.MESSAGES[i],
            "observed": int(pooled[i]),
            "expected": float(expected),
            "standardized_residual": float(z_scores[i]),
            "chi_square_contribution": float(contributions[i]),
        }

    order = np.argsort(-contributions)
    top_k = min(10, MESSAGE_COUNT)
    top = [_row(int(i)) for i in order[:top_k]]

    def _flagged(threshold: float) -> list[dict]:
        return [_row(int(i)) for i in np.where(np.abs(z_scores) >= threshold)[0]]

    result = {
        "experiment": "pooled wrong-password experiment across multiple ciphertexts",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "git": collect_git_info(),
        "parameters": {
            "ciphertexts": n_ciphertexts,
            "guesses_per_ciphertext": guesses,
            "total_wrong_guesses": trials,
            "message_count": MESSAGE_COUNT,
            "password_kdf": "PBKDF2-HMAC-SHA256",
            "pbkdf2_iterations": honey.PBKDF2_ITERATIONS,
            "ci_level": ci_level,
            "bootstrap_replicates": n_boot,
            "bootstrap_method": "cluster bootstrap (resample ciphertexts with replacement)",
        },
        "pooled": {
            "trials": trials,
            "expected_count_per_message": float(expected),
            "expected_probability_per_message": uniform,
            "chi_square_statistic": chi2_stat,
            "degrees_of_freedom": MESSAGE_COUNT - 1,
            "chi_square_p_value": p_value,
            "total_variation_distance": tvd,
            "tvd_ci_lower": tvd_ci_lo,
            "tvd_ci_upper": tvd_ci_hi,
            "tvd_ci_level": ci_level,
            "counts": [int(c) for c in pooled],
            "standardized_residuals": [float(z) for z in z_scores],
            "chi_square_contributions": [float(c) for c in contributions],
        },
        "per_ciphertext": {
            "tvd": _quantiles(np.asarray(per_ct_tvds)),
            "distinct_messages": _quantiles_int(np.asarray(per_ct_distinct)),
        },
        "outliers": {
            "top_by_chi_square_contribution": top,
            "by_residual_threshold": {
                "abs_z_ge_2": _flagged(2.0),
                "abs_z_ge_3": _flagged(3.0),
                "bonferroni_threshold_abs_z": bonferroni_z,
                "bonferroni_outliers": _flagged(bonferroni_z),
            },
        },
        "runtime_seconds": time.perf_counter() - started,
        "interpretation_notes": [
            "Every wrong guess returns an in-domain sentence; the attacker has no built-in correctness oracle.",
            "The message model has only 112 entries; pooled statistics measure the prototype's wrong-password output distribution, not semantic plausibility.",
            "The cluster bootstrap resamples ciphertexts with replacement to account for within-ciphertext dependence.",
            "Random wrong passwords are not a model of targeted dictionary or side-information attacks.",
        ],
    }

    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ciphertexts", type=int, default=DEFAULT_CIPHERTEXTS)
    parser.add_argument("--guesses-per-ciphertext", type=int, default=DEFAULT_GUESSES)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--ci-level", type=float, default=DEFAULT_CI_LEVEL)
    parser.add_argument("--bootstrap-replicates", type=int, default=DEFAULT_BOOTSTRAP)
    args = parser.parse_args()

    try:
        result = run(
            args.ciphertexts,
            args.guesses_per_ciphertext,
            args.seed,
            args.output,
            args.ci_level,
            args.bootstrap_replicates,
        )
    except (ValueError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")

    pooled = result["pooled"]
    per_ct = result["per_ciphertext"]
    print(f"Wrote {args.output}")
    print(f"Pooled trials: {pooled['trials']:,}")
    print(
        f"Pooled chi-square: {pooled['chi_square_statistic']:.3f} "
        f"(df={pooled['degrees_of_freedom']}), p={pooled['chi_square_p_value']:.6g}"
    )
    print(
        f"Pooled TVD: {pooled['total_variation_distance']:.6f} "
        f"({args.ci_level:.0%} cluster-bootstrap CI "
        f"{pooled['tvd_ci_lower']:.6f}–{pooled['tvd_ci_upper']:.6f})"
    )
    tvd = per_ct["tvd"]
    print(
        f"Per-ciphertext TVD: min={tvd['min']:.4f}, median={tvd['median']:.4f}, "
        f"max={tvd['max']:.4f}, std={tvd['std']:.4f}"
    )
    distinct = per_ct["distinct_messages"]
    print(
        f"Per-ciphertext distinct messages: min={distinct['min']}, "
        f"median={distinct['median']:.1f}, max={distinct['max']}"
    )
    top = result["outliers"]["top_by_chi_square_contribution"][0]
    print(
        f"Largest pooled outlier: {top['message']!r} "
        f"(observed={top['observed']}, expected={top['expected']:.2f}, "
        f"z={top['standardized_residual']:+.3f})"
    )


if __name__ == "__main__":
    main()