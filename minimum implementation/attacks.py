"""Reproducible attacker-model experiments for the bounded honey demo.

These experiments measure properties of this prototype; they are not proofs of
security and do not model a general-purpose natural-language attacker.
"""
from __future__ import annotations
import argparse, hashlib, json, math, secrets, statistics, time
from collections import Counter
from pathlib import Path
import honey
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DEFAULT_OUT = Path(__file__).resolve().parent / "evaluation_results"

# A deliberately transparent, synthetic candidate list. Do not mistake it for
# a leaked-password corpus or a representative population password model.
SYNTHETIC_DICTIONARY = [
    "password", "123456", "qwerty", "letmein", "welcome", "iloveyou",
    "admin", "monkey", "dragon", "football", "baseball", "sunshine",
    "trustno1", "abc123", "password1", "welcome1", "summer2026",
    "knoxville", "computer", "student", "changeme", "hello123",
    "correct-horse-battery-staple", "P@ssw0rd!", "hunter2",
]


def feature(message: str, field: str) -> str:
    parts = message.removeprefix("Meet me at ").removesuffix(".").split()
    # location on day at time
    return {"location": parts[0], "day": parts[2], "time": parts[4]}[field]


def side_information(output: Path) -> dict:
    """Compute candidate-set reduction from known message attributes."""
    rows = []
    for field in ("none", "location", "day", "time", "location+day", "day+time"):
        counts = Counter()
        for message in honey.MESSAGES:
            if field == "none": key = "all"
            else:
                fields = field.split("+")
                key = tuple(feature(message, f) for f in fields)
            counts[key] += 1
        rows.append({"known_fields": field, "candidate_messages_remaining": max(counts.values()),
                     "candidate_fraction": max(counts.values()) / honey.MESSAGE_COUNT,
                     "idealized_log2_search_space_bits": math.log2(max(counts.values()))})
    result = {"experiment": "structural side-information candidate reduction",
              "message_count": honey.MESSAGE_COUNT,
              "interpretation": "Counts compatible messages only; assumes a uniform prior and does not infer whether an observed decoy is true.",
              "results": rows}
    output.mkdir(parents=True, exist_ok=True)
    (output / "side_information.json").write_text(json.dumps(result, indent=2)+"\n")
    labels=[r["known_fields"].replace("+", " + ") for r in rows]
    values=[r["candidate_messages_remaining"] for r in rows]
    plt.figure(figsize=(8,4.5)); plt.bar(labels,values)
    plt.ylabel("Compatible messages remaining"); plt.title("Message-space reduction from side information")
    plt.xticks(rotation=25,ha="right"); plt.tight_layout()
    plt.savefig(output/"side_information.png",dpi=160); plt.close()
    return result


def dictionary_attack(trials: int, output: Path) -> dict:
    """Apply synthetic dictionary guesses to independent demo ciphertexts.

    The correct password is chosen from a deterministic synthetic list. The
    attacker tries the list in order; recovery rank is recorded. Wrong guesses
    always yield in-domain decoys, so no validity oracle exists in this demo.
    """
    rng = secrets.SystemRandom()
    passwords = SYNTHETIC_DICTIONARY
    rank_counts = Counter()
    decoy_counts = Counter()
    recovered = 0
    started = time.perf_counter()
    for i in range(trials):
        true_rank = rng.randrange(1, len(passwords)+1)
        true_password = passwords[true_rank-1]
        message = honey.MESSAGES[rng.randrange(honey.MESSAGE_COUNT)]
        record = honey.encrypt(message, true_password)
        record.pop("example", None)
        # Each dictionary candidate is tried in list order. In an actual HE
        # setting there is no built-in test for which candidate is correct.
        # We record the true rank for password-population analysis only.
        rank_counts[true_rank] += 1
        for candidate in passwords[:true_rank-1]:
            decoy = honey.decrypt(record, candidate)
            decoy_counts[decoy] += 1
        if honey.decrypt(record, true_password) == message:
            recovered += 1
    runtime = time.perf_counter()-started
    result = {
        "experiment": "synthetic dictionary rank and wrong-guess output study",
        "trials": trials, "dictionary_size": len(passwords),
        "password_population": "uniformly sampled from an explicitly synthetic 25-entry list; not representative of real users",
        "attacker_observation": "No verifier: every candidate produces a valid message; true rank is known only to the evaluator.",
        "correct_recovery_checks": recovered,
        "mean_true_password_rank": statistics.mean([rank for rank,count in rank_counts.items() for _ in range(count)]),
        "median_true_password_rank": statistics.median([rank for rank,count in rank_counts.items() for _ in range(count)]),
        "rank_histogram": {str(k):rank_counts[k] for k in range(1,len(passwords)+1)},
        "wrong_guess_decoded_outputs": sum(decoy_counts.values()),
        "distinct_wrong_guess_outputs": len(decoy_counts),
        "wrong_guess_output_top_10": decoy_counts.most_common(10),
        "runtime_seconds": runtime,
        "caveat": "This does not demonstrate that an attacker can identify the correct password. Without external validation or side information, the outputs have no correctness flag. Synthetic passwords are not a measured human distribution."
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "dictionary_attack.json").write_text(json.dumps(result, indent=2)+"\n")
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--trials", type=int, default=12)
    p.add_argument("--output", type=Path, default=DEFAULT_OUT)
    a=p.parse_args()
    if a.trials < 1: p.error("--trials must be positive")
    side=side_information(a.output)
    dictionary=dictionary_attack(a.trials,a.output)
    print(json.dumps({"side_information":side,"dictionary_attack":dictionary},indent=2))

if __name__=="__main__": main()
