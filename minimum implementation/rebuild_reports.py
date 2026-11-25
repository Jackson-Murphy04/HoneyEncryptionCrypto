#!/usr/bin/env python3
"""Rebuild EXTENDED_RESULTS.md and the README results table from JSON outputs.

Every displayed number is copied verbatim from a JSON file in
`evaluation_results/`. Nothing is invented. Missing JSON files are skipped
(their section is omitted) and noted on stderr. The README update only
touches the region between `<!-- BEGIN GENERATED RESULTS -->` and
`<!-- END GENERATED RESULTS -->`.

Usage:
    python rebuild_reports.py
    python rebuild_reports.py --results-dir path/to/evaluation_results
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_RESULTS = HERE / "evaluation_results"
DEFAULT_README = HERE.parent / "README.md"
DEFAULT_EXTENDED = DEFAULT_RESULTS / "EXTENDED_RESULTS.md"

BEGIN_MARKER = "\n<!-- BEGIN GENERATED RESULTS -->\n"
END_MARKER = "\n<!-- END GENERATED RESULTS -->\n"

RESULTS_FILE = "results.json"
WEIGHTED_FILE = "weighted_dte_results.json"
SIDE_FILE = "side_information.json"
DICTIONARY_FILE = "dictionary_attack.json"
POOLED_FILE = "pooled_wrong_password_results.json"


def _load(path: Path) -> dict | None:
    if not path.is_file():
        print(f"note: {path.name} not found; its section will be omitted", file=sys.stderr)
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"warning: {path.name} is not valid JSON: {exc}", file=sys.stderr)
        return None


def _n(x: float, digits: int = 6) -> str:
    return f"{float(x):.{digits}f}"


def _i(x) -> str:
    return f"{int(round(x)):,}"


def _results_table(results, weighted, pooled) -> str:
    rows = []
    if results is not None:
        rows.append(("Uniform random seeds", results["random_seed_experiment"]))
        rows.append((
            "Random incorrect passwords (single ciphertext)",
            results["wrong_password_experiment"],
        ))
    if pooled is not None:
        rows.append((
            f"Pooled wrong passwords ({pooled['parameters']['ciphertexts']} ciphertexts)",
            pooled["pooled"],
        ))
    if weighted is not None:
        rows.append(("Weighted random seeds", weighted))
    if not rows:
        return "*No result JSON files found. Run the evaluation scripts first.*"

    lines = [
        "| Experiment | Trials | Pearson chi-square | df | p-value | TVD |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, r in rows:
        lines.append(
            f"| {name} | {_i(r['trials'])} | {_n(r['chi_square_statistic'], 3)} | "
            f"{r['degrees_of_freedom']} | {_n(r['chi_square_p_value'], 6)} | "
            f"{_n(r['total_variation_distance'], 6)} |"
        )
    return "\n".join(lines)


def _section_weighted(w: dict) -> str:
    return f"""## Non-uniform weighted DTE

- Trials: {_i(w['trials'])} random {w.get('seed_bits', 256)}-bit seeds
- Target: {w.get('synthetic_prior', 'declared synthetic prior')}
- Pearson chi-square: {_n(w['chi_square_statistic'], 3)} ({w['degrees_of_freedom']} degrees of freedom)
- p-value: {_n(w['chi_square_p_value'], 6)}
- Total variation distance: {_n(w['total_variation_distance'], 6)}
- Expected category counts: approximately {w['min_expected_count']:.0f} to {w['max_expected_count']:.0f}
- Observed category counts: {w['min_observed_count']} to {w['max_observed_count']}

A large p-value means this sample did not provide evidence against the declared
synthetic prior. It does not establish that the weights match real messages.
The weighted DTE is standalone and is not connected to the PBKDF2/XOR
password wrapper.
"""


def _section_side_info(side: dict) -> str:
    lines = [
        "## Structural side information",
        "",
        f"- Message model size: {side['message_count']}",
        f"- Note: {side['interpretation']}",
        "",
        "| Known field(s) | Compatible messages remaining | Fraction of original set |",
        "|---|---:|---:|",
    ]
    for row in side["results"]:
        lines.append(
            f"| {row['known_fields']} | {row['candidate_messages_remaining']} | "
            f"{row['candidate_fraction']:.2%} |"
        )
    return "\n".join(lines) + "\n"


def _section_dictionary(d: dict) -> str:
    return f"""## Synthetic dictionary pilot

- Trials: {_i(d['trials'])}
- Candidate list size: {d['dictionary_size']} strings
- Password population: {d['password_population']}
- Correct-password recovery checks: {d['correct_recovery_checks']}/{d['trials']}
- Mean true-password rank: {_n(d['mean_true_password_rank'], 2)}
- Median true-password rank: {_n(d['median_true_password_rank'], 1)}
- Wrong-guess decryptions performed: {d['wrong_guess_decoded_outputs']}
- Distinct wrong-guess output sentences: {d['distinct_wrong_guess_outputs']}

{d.get('caveat', '')}
"""


def _section_pooled(p: dict) -> str:
    pooled = p["pooled"]
    per_ct = p["per_ciphertext"]
    top_rows = "\n".join(
        f"| {o['message']} | {o['observed']} | {o['expected']:.2f} | "
        f"{o['standardized_residual']:+.3f} | {o['chi_square_contribution']:.3f} |"
        for o in p["outliers"]["top_by_chi_square_contribution"]
    )
    bonf = p["outliers"]["by_residual_threshold"]
    alpha = 1.0 - pooled["tvd_ci_level"]
    return f"""## Pooled wrong-password experiment

- Ciphertexts: {p['parameters']['ciphertexts']}
- Guesses per ciphertext: {p['parameters']['guesses_per_ciphertext']}
- Total wrong guesses: {_i(pooled['trials'])}
- Pooled chi-square: {_n(pooled['chi_square_statistic'], 3)} (df={pooled['degrees_of_freedom']})
- Pooled p-value: {_n(pooled['chi_square_p_value'], 6)}
- Pooled TVD: {_n(pooled['total_variation_distance'], 6)} ({pooled['tvd_ci_level']:.0%} cluster-bootstrap CI {_n(pooled['tvd_ci_lower'], 6)}–{_n(pooled['tvd_ci_upper'], 6)})

### Per-ciphertext variation

- Per-ciphertext TVD: min {_n(per_ct['tvd']['min'], 4)}, median {_n(per_ct['tvd']['median'], 4)}, max {_n(per_ct['tvd']['max'], 4)}, std {_n(per_ct['tvd']['std'], 4)}
- Per-ciphertext distinct decoded messages: min {per_ct['distinct_messages']['min']}, median {_n(per_ct['distinct_messages']['median'], 1)}, max {per_ct['distinct_messages']['max']}

### Pooled outliers

Top messages by contribution to the pooled chi-square statistic:

| Message | Observed | Expected | Std. residual | Chi-square contribution |
|---|---:|---:|---:|---:|
{top_rows}

- Bonferroni-corrected |z| threshold at α={alpha:.2f}: {_n(bonf['bonferroni_threshold_abs_z'], 3)}
- Messages with |z| ≥ 2: {len(bonf['abs_z_ge_2'])}
- Messages with |z| ≥ 3: {len(bonf['abs_z_ge_3'])}
- Messages beyond Bonferroni threshold: {len(bonf['bonferroni_outliers'])}

{p['interpretation_notes'][0]}
"""


def _section_files(weighted, side, dictionary, pooled) -> str:
    names = [
        RESULTS_FILE, WEIGHTED_FILE, SIDE_FILE, DICTIONARY_FILE, POOLED_FILE,
        "message_frequencies.csv", "random_seed_distribution.png",
        "wrong_password_distribution.png",
    ]
    lines = ["## Files", "", "Files read by this rebuild:", ""]
    for name in names:
        present = (DEFAULT_RESULTS / name).is_file()
        lines.append(f"- `{name}`{'' if present else ' *(missing)*'}")
    return "\n".join(lines) + "\n"


def _extended_markdown(results, weighted, side, dictionary, pooled) -> str:
    parts = [
        "# Extended experiment results\n",
        "These experiments extend the original `RESULTS.md`. They are educational "
        "measurements of this prototype, not proofs of honey-encryption security.\n",
    ]
    if weighted is not None:
        parts.append(_section_weighted(weighted))
    if side is not None:
        parts.append(_section_side_info(side))
    if dictionary is not None:
        parts.append(_section_dictionary(dictionary))
    if pooled is not None:
        parts.append(_section_pooled(pooled))
    parts.append(
        "## Conventional authenticated-encryption baseline\n\n"
        "The separate AES-256-GCM/scrypt baseline passed correct-password round-trip "
        "testing. A wrong password raised an authentication-tag failure. This is an "
        "expected contrast with the HE-inspired demo, which intentionally produces a "
        "decoy sentence for a wrong password. The comparison does not establish "
        "equivalent security properties.\n"
    )
    parts.append(_section_files(weighted, side, dictionary, pooled))
    return "\n".join(parts)


def _replace_between(text: str, begin: str, end: str, new_content: str, path: Path) -> str:
    if begin not in text or end not in text:
        raise SystemExit(
            f"error: markers not found in {path}. Expected:\n  {begin}\n  {end}"
        )
    before, rest = text.split(begin, 1)
    _, after = rest.split(end, 1)
    return f"{before}{begin}{new_content}\n{end}{after}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--readme", type=Path, default=DEFAULT_README)
    parser.add_argument("--extended", type=Path, default=DEFAULT_EXTENDED)
    args = parser.parse_args()

    results = _load(args.results_dir / RESULTS_FILE)
    weighted = _load(args.results_dir / WEIGHTED_FILE)
    side = _load(args.results_dir / SIDE_FILE)
    dictionary = _load(args.results_dir / DICTIONARY_FILE)
    pooled = _load(args.results_dir / POOLED_FILE)

    # EXTENDED_RESULTS.md
    args.extended.write_text(
        _extended_markdown(results, weighted, side, dictionary, pooled),
        encoding="utf-8",
    )
    print(f"Wrote {args.extended}")

    # README results table between markers.
    table = _results_table(results, weighted, pooled)
    readme_text = args.readme.read_text(encoding="utf-8")
    updated = _replace_between(readme_text, BEGIN_MARKER, END_MARKER, table, args.readme)
    args.readme.write_text(updated, encoding="utf-8")
    print(f"Updated {args.readme} between generated-results markers")


if __name__ == "__main__":
    main()