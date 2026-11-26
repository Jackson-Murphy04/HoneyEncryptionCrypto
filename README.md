# Honey Encryption for Structured English Messages

An educational cryptography project that implements and evaluates a honey-encryption-inspired construction for a finite set of meeting messages. It is a research/teaching artifact, **not a production security tool**.

## Research question

Can a distribution-transforming encoder (DTE) map incorrect-password decryptions into a restricted set of structured English messages, and how sensitive is that goal to the assumed message distribution and attacker side information?

The original prototype supports 112 sentences of the form `Meet me at [location] on [day] at [time].` (4 locations × 7 days × 4 times). The uniform version assigns probability 1/112 to each sentence. The extension adds an explicitly synthetic non-uniform prior.

## Important security warning

The original password layer derives a 32-byte mask with PBKDF2-HMAC-SHA256 (200,000 iterations) and XORs it with the DTE seed. It has **no authentication tag or integrity protection**. Every valid-length password guess decodes to a sentence because the DTE is total. The CLI's example JSON also stores the original plaintext and password as teaching metadata. **Do not use this prototype to protect real data or passwords.** It is not a formally validated honey-encryption implementation.

A separate AES-256-GCM/scrypt baseline is included solely to contrast conventional authenticated encryption: wrong passwords raise an authentication failure instead of producing decoys.

## Repository layout

```text
.
├── README.md
├── paper/
│   ├── main.tex
│   └── references.bib
└── minimum implementation/
    ├── honey.py                     # Original uniform DTE + PBKDF2/XOR CLI
    ├── weighted_dte.py              # Synthetic integer-weight DTE
    ├── evaluate.py                  # Uniform seed / random-wrong-password study
    ├── weighted_evaluate.py         # Non-uniform DTE seed-distribution study
    ├── attacks.py                   # Side-information + synthetic dictionary pilot
    ├── baseline.py                  # AES-GCM/scrypt comparison
    ├── pooled_wrong_password.py     # Pooled wrong-password experiment across many ciphertexts
    ├── rebuild_reports.py           # Regenerate EXTENDED_RESULTS.md + README results table
    ├── _eval_helpers.py             # Shared git / seeded-RNG helpers
    ├── test_honey.py
    ├── test_extensions.py
    ├── test_baseline.py
    ├── PROTOTYPE.md
    └── evaluation_results/          # JSON, CSV, plots, and captured experiment outputs
```

## Setup

Python 3.10+ is required. From `minimum implementation/`:

```bash
python -m pip install -r requirements.txt
```

## Run the prototype

```bash
python honey.py messages
python honey.py encrypt "Meet me at library on Monday at 9am." demo.json
python honey.py decrypt demo.json
```

The CLI prompts for passwords without echo. Example files contain plaintext teaching metadata; use demonstration passwords only.

## Run tests

```bash
python -m unittest -v
```

The expanded test suite checks uniform and weighted DTE boundaries, round trips for all 112 messages, target-probability normalization, JSON behavior, metadata independence, and the AES-GCM baseline's authentication behavior.

## Reproduce experiments

```bash
# Original uniform DTE / wrong random password experiment
python evaluate.py

# Same experiment, reproducible via a seeded PRNG for sampling
python evaluate.py --seed 12345

# Pooled wrong-password experiment across many ciphertexts
python pooled_wrong_password.py --seed 12345

# Synthetic non-uniform prior: default 560,000 random seeds
python weighted_evaluate.py

# Side-information counts and a small synthetic password-dictionary pilot
python attacks.py --trials 12

# Rebuild EXTENDED_RESULTS.md and the README results table from JSON
python rebuild_reports.py
```

`rebuild_reports.py` reads the JSON files under `evaluation_results/` and
regenerates `EXTENDED_RESULTS.md` plus the `<!-- BEGIN GENERATED RESULTS -->` …
`<!-- END GENERATED RESULTS -->` block in this README. Every displayed number is
copied verbatim from a JSON file; missing JSONs are skipped and noted on stderr
rather than filled with placeholders.

The dictionary pilot is intentionally small because every guess performs PBKDF2. Its 25-entry candidate list is synthetic and is **not** representative of real user passwords. It measures true password ranks and the fact that every guess yields a message; it does not give the attacker an oracle for identifying the correct guess.

## Captured results

The included `evaluation_results/` directory contains the exact output files. Selected measurements:

<!-- BEGIN GENERATED RESULTS -->
| Experiment | Trials | Pearson chi-square | df | p-value | TVD |
|---|---:|---:|---:|---:|---:|
| Uniform random seeds | 1,120,000 | 117.444 | 111 | 0.319549 | 0.004047 |
| Random incorrect passwords (single ciphertext) | 560 | 100.000 | 111 | 0.763939 | 0.162500 |
| Pooled wrong passwords (5 ciphertexts) | 100 | 128.480 | 111 | 0.122840 | 0.437500 |
| Weighted random seeds | 560,000 | 102.215 | 111 | 0.712551 | 0.005248 |

<!-- END GENERATED RESULTS -->

`evaluate.py` and `pooled_wrong_password.py` additionally report a
percentile-bootstrap confidence interval for the TVD, both in the per-run
`results.json` / `pooled_wrong_password_results.json` and in the human-readable
`RESULTS.md` written by `evaluate.py`. The interval quantifies sampling
uncertainty of the TVD *estimate* — it is not a test of equality with uniform
(the chi-square p-value plays that role).

The original single-ciphertext wrong-password experiment has an expected count
of five per message, so its chi-square approximation is fragile. It also uses
random high-entropy guesses against one fixed ciphertext/salt. The weighted-DTE
experiment checks only whether a decoder follows its **hand-authored synthetic
prior**; it is not evidence that the prior models real conversations. The
pooled wrong-password experiment targets that single-ciphertext limitation by
pooling over many independent ciphertexts and reporting per-ciphertext
dispersion as well as pooled outlier diagnostics.

The structural side-information calculation is exact for the finite message set:

| Known field(s) | Compatible messages remaining |
|---|---:|
| None | 112 |
| Location | 28 |
| Day | 16 |
| Time | 28 |
| Location + day | 4 |
| Day + time | 4 |

These counts show how contextual knowledge reduces the candidate space. They do
not alone show that an attacker can identify the genuine message.

## Interpretation and limitations

- Every output belongs to the 112-message set by construction. This is format validity, not proof of semantic plausibility.
- A good DTE requires a realistic message distribution. The weighted prior is illustrative and not trained on collected communication data.
- Side information such as known day/location can strongly reduce the candidate set.
- The dictionary experiment is a small synthetic pilot, not a human-password study.
- The password layer is unauthenticated and has not undergone cryptographic review.
- The project does not claim formal HE security, indistinguishability, or unrestricted-English support.

See `paper/main.tex` for the ACM-style report and `minimum implementation/PROTOTYPE.md` for implementation notes.