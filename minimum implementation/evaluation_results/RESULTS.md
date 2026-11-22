# Experimental results

Generated: 2026-11-22T03:21:01.899258+00:00

## Configuration

- Supported messages: 112
- Seed width: 256 bits
- Expected probability per message: 0.89285714%
- PBKDF2-HMAC-SHA256 iterations: 200,000
- Random seed trials: 1,120,000
- Distinct incorrect-password trials: 560
- Wrong-password test: one fixed ciphertext and salt; random unique candidate passwords

## Random 256-bit seed experiment

- Runtime: 0.680 seconds
- Expected count per message: 10000.000
- Observed count range: 9698–10221
- Chi-square: 117.444 (df=111)
- p-value: 0.319549
- Total variation distance from uniform: 0.004047
- Maximum absolute standardized residual: 3.020

## Incorrect-password experiment

- Runtime: 17.263 seconds
- Expected count per message: 5.000
- Observed count range: 1–12
- Chi-square: 100.000 (df=111)
- p-value: 0.763939
- Total variation distance from uniform: 0.162500
- Maximum absolute standardized residual: 3.130
- Correct-password recovery check: PASS

## Interpretation

The chi-square test compares the observed counts with the uniform expectation of 1/112 per message. A large p-value means this sample did not provide evidence against the uniform model; it is not proof of uniformity. The random-seed experiment measures the DTE decoder directly. The incorrect-password experiment additionally depends on PBKDF2-derived masks and uses random high-entropy candidate passwords, not human-selected passwords or a realistic attacker dictionary.

Every output is guaranteed by the decoder to be one of the 112 supported sentences. This format-validity property is built into the bounded decoder and does not establish that the sentence is semantically plausible, indistinguishable from the original, or secure against side information. The small message space also means an incorrect password can produce the original sentence by chance.

See `results.json` for full parameters and statistics, `message_frequencies.csv` for per-message counts, and the PNG files for plots. Do not interpret a single experiment as a cryptographic security proof.
