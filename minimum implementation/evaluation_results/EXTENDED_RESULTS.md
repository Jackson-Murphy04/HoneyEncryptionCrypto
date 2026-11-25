# Extended experiment results

These experiments extend the original `RESULTS.md`. They are educational measurements of this prototype, not proofs of honey-encryption security.

## Non-uniform weighted DTE

- Trials: 560,000 random 256-bit seeds
- Target: product of declared location, weekday, and time weights in weighted_dte.py
- Pearson chi-square: 102.215 (111 degrees of freedom)
- p-value: 0.712551
- Total variation distance: 0.005248
- Expected category counts: approximately 1103 to 11494
- Observed category counts: 1041 to 11666

A large p-value means this sample did not provide evidence against the declared
synthetic prior. It does not establish that the weights match real messages.
The weighted DTE is standalone and is not connected to the PBKDF2/XOR
password wrapper.

## Structural side information

- Message model size: 112
- Note: Counts compatible messages only; assumes a uniform prior and does not infer whether an observed decoy is true.

| Known field(s) | Compatible messages remaining | Fraction of original set |
|---|---:|---:|
| none | 112 | 100.00% |
| location | 28 | 25.00% |
| day | 16 | 14.29% |
| time | 28 | 25.00% |
| location+day | 4 | 3.57% |
| day+time | 4 | 3.57% |

## Synthetic dictionary pilot

- Trials: 12
- Candidate list size: 25 strings
- Password population: uniformly sampled from an explicitly synthetic 25-entry list; not representative of real users
- Correct-password recovery checks: 12/12
- Mean true-password rank: 15.00
- Median true-password rank: 18.0
- Wrong-guess decryptions performed: 168
- Distinct wrong-guess output sentences: 89

This does not demonstrate that an attacker can identify the correct password. Without external validation or side information, the outputs have no correctness flag. Synthetic passwords are not a measured human distribution.

## Pooled wrong-password experiment

- Ciphertexts: 5
- Guesses per ciphertext: 20
- Total wrong guesses: 100
- Pooled chi-square: 128.480 (df=111)
- Pooled p-value: 0.122840
- Pooled TVD: 0.437500 (95% cluster-bootstrap CI 0.437500–0.732143)

### Per-ciphertext variation

- Per-ciphertext TVD: min 0.8304, median 0.8393, max 0.8571, std 0.0120
- Per-ciphertext distinct decoded messages: min 16, median 18.0, max 19

### Pooled outliers

Top messages by contribution to the pooled chi-square statistic:

| Message | Observed | Expected | Std. residual | Chi-square contribution |
|---|---:|---:|---:|---:|
| Meet me at office on Sunday at 12pm. | 5 | 0.89 | +4.347 | 18.893 |
| Meet me at park on Sunday at 12pm. | 4 | 0.89 | +3.288 | 10.813 |
| Meet me at cafe on Saturday at 6pm. | 3 | 0.89 | +2.230 | 4.973 |
| Meet me at park on Thursday at 12pm. | 3 | 0.89 | +2.230 | 4.973 |
| Meet me at library on Sunday at 12pm. | 3 | 0.89 | +2.230 | 4.973 |
| Meet me at library on Friday at 6pm. | 3 | 0.89 | +2.230 | 4.973 |
| Meet me at cafe on Saturday at 12pm. | 3 | 0.89 | +2.230 | 4.973 |
| Meet me at library on Tuesday at 3pm. | 3 | 0.89 | +2.230 | 4.973 |
| Meet me at cafe on Monday at 9am. | 2 | 0.89 | +1.172 | 1.373 |
| Meet me at park on Saturday at 3pm. | 2 | 0.89 | +1.172 | 1.373 |

- Bonferroni-corrected |z| threshold at α=0.05: 3.511
- Messages with |z| ≥ 2: 8
- Messages with |z| ≥ 3: 2
- Messages beyond Bonferroni threshold: 1

Every wrong guess returns an in-domain sentence; the attacker has no built-in correctness oracle.

## Conventional authenticated-encryption baseline

The separate AES-256-GCM/scrypt baseline passed correct-password round-trip testing. A wrong password raised an authentication-tag failure. This is an expected contrast with the HE-inspired demo, which intentionally produces a decoy sentence for a wrong password. The comparison does not establish equivalent security properties.

## Files

Files read by this rebuild:

- `results.json`
- `weighted_dte_results.json`
- `side_information.json`
- `dictionary_attack.json`
- `pooled_wrong_password_results.json`
- `message_frequencies.csv`
- `random_seed_distribution.png`
- `wrong_password_distribution.png`
