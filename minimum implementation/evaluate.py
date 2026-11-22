"""Reproducible distribution evaluation for the bounded honey-encryption demo.

This is a statistical experiment, not a proof of honey-encryption security.
Random seeds are sampled with Python's OS-backed secrets module. Wrong-password
trials use distinct random candidate passwords and the prototype's real PBKDF2
password-mask/decode path.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import secrets
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import chisquare

import honey


DEFAULT_SEED_TRIALS = 1_120_000
DEFAULT_WRONG_PASSWORD_TRIALS = 560
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "evaluation_results"
MESSAGE_INDEX = {message: index for index, message in enumerate(honey.MESSAGES)}


def summarize(counts: Counter[int], trials: int) -> dict:
    expected = trials / honey.MESSAGE_COUNT
    observed = [counts.get(i, 0) for i in range(honey.MESSAGE_COUNT)]
    statistic, p_value = chisquare(observed, f_exp=[expected] * honey.MESSAGE_COUNT)
    residuals = [(value - expected) / math.sqrt(expected) for value in observed]
    absolute_errors = [abs(value - expected) for value in observed]
    return {
        "trials": trials,
        "expected_count_per_message": expected,
        "expected_probability": 1 / honey.MESSAGE_COUNT,
        "chi_square_statistic": float(statistic),
        "degrees_of_freedom": honey.MESSAGE_COUNT - 1,
        "chi_square_p_value": float(p_value),
        "min_count": min(observed),
        "max_count": max(observed),
        "max_absolute_standardized_residual": max(abs(x) for x in residuals),
        "total_variation_distance": 0.5 * sum(
            abs(value / trials - 1 / honey.MESSAGE_COUNT) for value in observed
        ),
        "counts": observed,
        "standardized_residuals": residuals,
        "absolute_count_errors": absolute_errors,
    }


def write_csv(path: Path, seed_summary: dict, wrong_summary: dict) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "message_index", "message", "expected_probability",
            "seed_observed_count", "seed_observed_probability",
            "seed_standardized_residual", "wrong_password_observed_count",
            "wrong_password_observed_probability", "wrong_password_standardized_residual",
        ])
        for i, message in enumerate(honey.MESSAGES):
            writer.writerow([
                i, message, 1 / honey.MESSAGE_COUNT,
                seed_summary["counts"][i],
                seed_summary["counts"][i] / seed_summary["trials"],
                seed_summary["standardized_residuals"][i],
                wrong_summary["counts"][i],
                wrong_summary["counts"][i] / wrong_summary["trials"],
                wrong_summary["standardized_residuals"][i],
            ])


def plot_distribution(path: Path, title: str, summary: dict) -> None:
    indices = list(range(honey.MESSAGE_COUNT))
    expected = summary["expected_count_per_message"]
    plt.figure(figsize=(15, 5.5))
    plt.bar(indices, summary["counts"], width=0.85)
    plt.axhline(expected, linestyle="--", linewidth=1.5,
                label=f"Expected count = {expected:,.2f}")
    plt.xlabel("Message index (see message_frequencies.csv for sentence)")
    plt.ylabel("Observed count")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def run(seed_trials: int, wrong_trials: int, output: Path) -> dict:
    if seed_trials < honey.MESSAGE_COUNT:
        raise ValueError(f"seed trials must be at least {honey.MESSAGE_COUNT}")
    if wrong_trials < honey.MESSAGE_COUNT:
        raise ValueError(f"wrong-password trials must be at least {honey.MESSAGE_COUNT}")

    output.mkdir(parents=True, exist_ok=True)
    started_all = time.perf_counter()

    # Experiment A: sample the full 256-bit seed space using OS-backed entropy.
    started = time.perf_counter()
    seed_counts: Counter[int] = Counter()
    for _ in range(seed_trials):
        seed = secrets.token_bytes(honey.SEED_BYTES)
        decoded = honey.decode(seed)
        seed_counts[MESSAGE_INDEX[decoded]] += 1
    seed_runtime = time.perf_counter() - started
    seed_summary = summarize(seed_counts, seed_trials)

    # Experiment B: encrypt one known message once, then try distinct random
    # wrong passwords against that same salt/ciphertext. Candidate passwords
    # are never saved; only decoded-message counts are retained.
    original_message = honey.MESSAGES[0]
    correct_password = "evaluation-only-correct-password"
    record = honey.encrypt(original_message, correct_password)
    record.pop("example", None)  # Do not retain the plaintext/password metadata.
    wrong_counts: Counter[int] = Counter()
    seen_candidates: set[str] = set()
    started = time.perf_counter()
    while len(seen_candidates) < wrong_trials:
        candidate = "wrong-" + secrets.token_hex(16)
        if candidate == correct_password or candidate in seen_candidates:
            continue
        seen_candidates.add(candidate)
        decoded = honey.decrypt(record, candidate)
        wrong_counts[MESSAGE_INDEX[decoded]] += 1
    wrong_runtime = time.perf_counter() - started
    wrong_summary = summarize(wrong_counts, wrong_trials)

    # Sanity-check the exact known-answer path outside the sampled wrong guesses.
    correct_recovery = honey.decrypt(record, correct_password) == original_message
    if not correct_recovery:
        raise AssertionError("Correct-password recovery failed")

    write_csv(output / "message_frequencies.csv", seed_summary, wrong_summary)
    plot_distribution(
        output / "random_seed_distribution.png",
        "Uniform random 256-bit seeds decoded across 112 messages",
        seed_summary,
    )
    plot_distribution(
        output / "wrong_password_distribution.png",
        "Outputs from distinct random incorrect-password guesses",
        wrong_summary,
    )

    result = {
        "experiment": "Honey Encryption structured-message distribution evaluation",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "implementation": platform.python_implementation(),
        },
        "parameters": {
            "message_count": honey.MESSAGE_COUNT,
            "seed_bits": honey.SEED_BYTES * 8,
            "salt_bytes": honey.SALT_BYTES,
            "password_kdf": "PBKDF2-HMAC-SHA256",
            "pbkdf2_iterations": honey.PBKDF2_ITERATIONS,
            "derived_key_bytes": honey.SEED_BYTES,
            "expected_probability_per_message": 1 / honey.MESSAGE_COUNT,
            "seed_sampling": "secrets.token_bytes (OS-backed randomness)",
            "wrong_password_sampling": "distinct 128-bit random suffixes; same ciphertext and salt",
            "original_message_for_wrong_password_test": original_message,
            "correct_password_recovery_check": correct_recovery,
        },
        "random_seed_experiment": {
            **{k: v for k, v in seed_summary.items() if k not in {"counts", "standardized_residuals", "absolute_count_errors"}},
            "runtime_seconds": seed_runtime,
        },
        "wrong_password_experiment": {
            **{k: v for k, v in wrong_summary.items() if k not in {"counts", "standardized_residuals", "absolute_count_errors"}},
            "runtime_seconds": wrong_runtime,
        },
        "total_runtime_seconds": time.perf_counter() - started_all,
        "interpretation_notes": [
            "A chi-square p-value is not the probability that the null hypothesis is true.",
            "A large p-value means this sample did not provide evidence against a uniform categorical distribution; it does not prove uniformity.",
            "The random-seed test directly samples the DTE decoder input space.",
            "The wrong-password test samples random candidate passwords through the actual PBKDF2/XOR/decode path, with one fixed ciphertext and salt.",
            "Random candidate passwords are not a model of human password choices or a targeted dictionary attack.",
            "The 112-message space is small; a plausible-looking output is not evidence of security for unrestricted English.",
        ],
    }
    (output / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    report = f"""# Experimental results

Generated: {result['generated_utc']}

## Configuration

- Supported messages: {honey.MESSAGE_COUNT}
- Seed width: {honey.SEED_BYTES * 8} bits
- Expected probability per message: {1 / honey.MESSAGE_COUNT:.8%}
- PBKDF2-HMAC-SHA256 iterations: {honey.PBKDF2_ITERATIONS:,}
- Random seed trials: {seed_trials:,}
- Distinct incorrect-password trials: {wrong_trials:,}
- Wrong-password test: one fixed ciphertext and salt; random unique candidate passwords

## Random 256-bit seed experiment

- Runtime: {seed_runtime:.3f} seconds
- Expected count per message: {seed_summary['expected_count_per_message']:.3f}
- Observed count range: {seed_summary['min_count']}–{seed_summary['max_count']}
- Chi-square: {seed_summary['chi_square_statistic']:.3f} (df={seed_summary['degrees_of_freedom']})
- p-value: {seed_summary['chi_square_p_value']:.6g}
- Total variation distance from uniform: {seed_summary['total_variation_distance']:.6f}
- Maximum absolute standardized residual: {seed_summary['max_absolute_standardized_residual']:.3f}

## Incorrect-password experiment

- Runtime: {wrong_runtime:.3f} seconds
- Expected count per message: {wrong_summary['expected_count_per_message']:.3f}
- Observed count range: {wrong_summary['min_count']}–{wrong_summary['max_count']}
- Chi-square: {wrong_summary['chi_square_statistic']:.3f} (df={wrong_summary['degrees_of_freedom']})
- p-value: {wrong_summary['chi_square_p_value']:.6g}
- Total variation distance from uniform: {wrong_summary['total_variation_distance']:.6f}
- Maximum absolute standardized residual: {wrong_summary['max_absolute_standardized_residual']:.3f}
- Correct-password recovery check: {'PASS' if correct_recovery else 'FAIL'}

## Interpretation

The chi-square test compares the observed counts with the uniform expectation of 1/{honey.MESSAGE_COUNT} per message. A large p-value means this sample did not provide evidence against the uniform model; it is not proof of uniformity. The random-seed experiment measures the DTE decoder directly. The incorrect-password experiment additionally depends on PBKDF2-derived masks and uses random high-entropy candidate passwords, not human-selected passwords or a realistic attacker dictionary.

Every output is guaranteed by the decoder to be one of the 112 supported sentences. This format-validity property is built into the bounded decoder and does not establish that the sentence is semantically plausible, indistinguishable from the original, or secure against side information. The small message space also means an incorrect password can produce the original sentence by chance.

See `results.json` for full parameters and statistics, `message_frequencies.csv` for per-message counts, and the PNG files for plots. Do not interpret a single experiment as a cryptographic security proof.
"""
    (output / "RESULTS.md").write_text(report, encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-trials", type=int, default=DEFAULT_SEED_TRIALS)
    parser.add_argument("--wrong-password-trials", type=int, default=DEFAULT_WRONG_PASSWORD_TRIALS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(args.seed_trials, args.wrong_password_trials, args.output)
    print(f"Results written to: {args.output}")
    print(f"Seed experiment: chi-square={result['random_seed_experiment']['chi_square_statistic']:.3f}, "
          f"p={result['random_seed_experiment']['chi_square_p_value']:.6g}, "
          f"runtime={result['random_seed_experiment']['runtime_seconds']:.3f}s")
    print(f"Wrong-password experiment: chi-square={result['wrong_password_experiment']['chi_square_statistic']:.3f}, "
          f"p={result['wrong_password_experiment']['chi_square_p_value']:.6g}, "
          f"runtime={result['wrong_password_experiment']['runtime_seconds']:.3f}s")


if __name__ == "__main__":
    main()
