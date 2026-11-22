# Honey Encryption for Structured English Messages

An educational cryptography project implementing and evaluating a honey-encryption-inspired construction for a restricted set of English meeting messages. The current prototype supports exactly 112 sentences of the form:

> Meet me at [location] on [day] at [time].

This repository contains a Python command-line prototype, correctness tests, and a reproducible statistical evaluation. It is a research/teaching artifact, **not a production security tool**.

## Project model

The message space is the Cartesian product of:

- Locations: `library`, `cafe`, `park`, `office` (4 values)
- Days: Monday through Sunday (7 values)
- Times: `9am`, `12pm`, `3pm`, `6pm` (4 values)

Thus there are `4 × 7 × 4 = 112` supported messages. The current model assigns each message the same target probability, `1/112 ≈ 0.892857%`.

The distribution-transforming encoder (DTE) assigns each message a contiguous interval in the 256-bit seed space. Encoding chooses a seed uniformly from that message's interval; decoding maps every 32-byte seed to exactly one supported sentence. Integer interval sizes differ by at most one because 112 does not divide `2^256` evenly. The resulting probability difference is negligible at this scale.

The password layer derives a 32-byte mask using PBKDF2-HMAC-SHA256 (200,000 iterations) and a fresh 16-byte salt, then XORs the mask with the DTE seed. Decryption applies the same mask and decodes the resulting seed. There is no password verifier or authentication tag: every syntactically valid password guess produces a sentence in the supported message set.

**Important construction limitation:** this is a compact educational prototype that demonstrates the DTE/decoy-output idea. It should not be described as a production-grade or formally validated honey-encryption scheme. The XOR/PBKDF2 layer has no integrity protection, and the prototype has not undergone cryptographic review.

## Repository layout

```text
.
├── README.md
└── minimum implementation/
    ├── honey.py                 # Message model, DTE, password layer, CLI
    ├── test_honey.py            # Unit tests
    ├── evaluate.py              # Distribution experiments and report generation
    ├── requirements.txt         # Evaluation plotting/statistics dependencies
    ├── PROTOTYPE.md             # CLI and design notes
    ├── examples/                # Example JSON records (if created by a user)
    └── evaluation_results/      # Captured experiment results and plots
```

## Setup

Python 3.10 or newer is required. The prototype and unit tests use the Python standard library. The evaluation script additionally uses SciPy and Matplotlib:

```bash
cd "minimum implementation"
python -m pip install -r requirements.txt
```

## Run the prototype

List supported messages:

```bash
python honey.py messages
```

Encrypt one exact supported sentence (the password is prompted without echo):

```bash
python honey.py encrypt "Meet me at library on Monday at 9am." demo.json
```

Try a password guess:

```bash
python honey.py decrypt demo.json
```

The example JSON includes plaintext/password teaching metadata for classroom comparison. Decryption ignores that metadata. **Use demonstration passwords only and do not treat these files as secure encrypted storage.** The metadata is stored in plaintext.

## Run correctness tests

```bash
python -m unittest -v
```

The tests cover all supported messages, seed interval boundaries, correct-password recovery, deterministic wrong-password decoding, fresh encryption randomness, metadata independence, JSON round trips, and overwrite protection.

## Run the statistical evaluation

From `minimum implementation/`:

```bash
python evaluate.py
```

The default experiment uses:

- 1,120,000 independently generated random 256-bit seeds;
- 560 distinct random incorrect-password guesses;
- 112 supported messages and an expected probability of `1/112` per message;
- PBKDF2-HMAC-SHA256 with 200,000 iterations and 16-byte salt;
- one fixed ciphertext and salt for the wrong-password experiment;
- OS-backed randomness through Python's `secrets` module.

To choose other sample sizes or an output directory:

```bash
python evaluate.py --seed-trials 1120000 --wrong-password-trials 560 --output evaluation_results
```

The script writes:

- `evaluation_results/results.json` — parameters, environment, runtimes, summary statistics, and interpretation notes;
- `evaluation_results/RESULTS.md` — human-readable results;
- `evaluation_results/message_frequencies.csv` — observed counts and probabilities for every message in both experiments;
- `evaluation_results/random_seed_distribution.png` — random-seed count plot;
- `evaluation_results/wrong_password_distribution.png` — incorrect-password count plot.

### Statistical method

For each experiment, the Pearson chi-square goodness-of-fit statistic compares the 112 observed counts with the equal expected count `n/112`. The report includes 111 degrees of freedom, the p-value, minimum/maximum counts, maximum absolute standardized residual, and total variation distance from the uniform distribution.

A large p-value means the sample did not provide evidence against the uniform model; it is **not** the probability that the null hypothesis is true and does not prove uniformity. The wrong-password experiment has an expected count of five per message, so its chi-square approximation should be interpreted cautiously. Increase `--wrong-password-trials` for a larger sample when runtime permits.

## Captured results

The included `minimum implementation/evaluation_results/` directory contains one completed run. The exact measurements and UTC timestamp are in `RESULTS.md` and `results.json`. In that run:

- Random-seed experiment: 1,120,000 trials; chi-square 117.444 (111 df); p = 0.319549; total variation distance = 0.004047; runtime = 0.680 s.
- Incorrect-password experiment: 560 trials; chi-square 100.000 (111 df); p = 0.763939; total variation distance = 0.162500; runtime = 17.263 s.
- Correct-password recovery check: passed.

These results are consistent with the uniform model for these samples, but they do not establish a security guarantee. In particular, the wrong-password experiment uses random high-entropy candidate passwords, not human password choices or a realistic attacker dictionary. It uses one fixed ciphertext/salt pair. All outputs are in the 112-message set by construction; that alone does not establish semantic plausibility or indistinguishability from the original message.

## Threat model and limitations

The intended experiment asks whether wrong password guesses produce outputs that look like members of the restricted message model. The prototype does not address a fully specified real-world attacker, and it does not model human communication probabilities. Its current uniform prior is deliberately simple. An attacker with side information (for example, knowing the meeting day or likely location) may assign different probabilities to candidate messages and distinguish the original from some decoys.

Other limitations include:

- only 112 fixed sentences and one sentence template;
- no empirically learned message distribution;
- no semantic model, grammar model, or variable-length English support;
- no authentication/integrity protection;
- random-password trials do not represent dictionary-based guessing;
- the experiment is statistical evidence from finite samples, not a proof of cryptographic security;
- the CLI's teaching metadata explicitly exposes the original message and password.

## Current status and next steps

Completed in this repository:

- [x] Defined 112 structured messages and a uniform target distribution.
- [x] Implemented a 256-bit DTE with randomized encoding and total decoding.
- [x] Added a PBKDF2-HMAC-SHA256 password mask and command-line demonstration.
- [x] Added unit tests for DTE boundaries and password recovery.
- [x] Tested 1,120,000 random seeds and saved per-message frequencies.
- [x] Tested 560 distinct incorrect passwords and saved per-message frequencies.
- [x] Recorded sample sizes, parameters, runtime, statistical summaries, and plots.
- [ ] Evaluate human-selected/dictionary password guesses and multiple original messages/salts.
- [ ] Model non-uniform message probabilities and attacker side information.
- [ ] Review formal honey-encryption constructions and compare the prototype against an authenticated-encryption baseline.
- [ ] Explore grammar/semantic models and the challenges of extending to unrestricted English.

## AI assistance

AI assistance was used to help inspect the initial repository, develop the evaluation harness, generate plots and machine-readable results, and draft documentation. The team should review the code and results, rerun the experiments on its own machine, and describe its AI use accurately in the final report.
