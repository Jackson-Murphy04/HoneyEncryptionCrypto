# Extended experiment results

These experiments extend the original `RESULTS.md`. They are educational measurements of this prototype, not proofs of honey-encryption security.

## Non-uniform weighted DTE

- Trials: 560,000 random 256-bit seeds
- Target: synthetic product prior over location, weekday, and time weights
- Pearson chi-square: 111.004 (111 degrees of freedom)
- p-value: 0.482054
- Total variation distance: 0.005621
- Expected category counts: approximately 1,103 to 11,494
- Observed category counts: 1,081 to 11,604

This is consistent with the declared synthetic prior at this sample size. It does not establish that the weights match real messages. The weighted DTE is currently standalone and is not connected to the PBKDF2/XOR password wrapper; this is a component-level distribution test, not an end-to-end weighted HE experiment.

## Structural side information

| Known fields | Compatible messages | Fraction of original set |
|---|---:|---:|
| None | 112 | 100.00% |
| Location | 28 | 25.00% |
| Day | 16 | 14.29% |
| Time | 28 | 25.00% |
| Location + day | 4 | 3.57% |
| Day + time | 4 | 3.57% |

This is an exact combinatorial count for the supported message model. It does not by itself identify the genuine message among the compatible candidates.

## Synthetic dictionary pilot

- Trials: 12
- Candidate list size: 25 hand-written strings
- Password population: uniform random selection from that list
- Correct-password recovery checks: 12/12
- Mean true-password rank: 10.25
- Median true-password rank: 11
- Wrong-guess decryptions performed: 111
- Distinct wrong-guess output sentences: 75

The list is not representative of actual human password choices. Every wrong guess returns an in-domain sentence, and the attacker has no built-in correctness oracle. The pilot is too small for general statistical claims.

## Conventional authenticated-encryption baseline

The separate AES-256-GCM/scrypt baseline passed correct-password round-trip testing. A wrong password raised an authentication-tag failure. This is an expected contrast with the HE-inspired demo, which intentionally produces a decoy sentence for a wrong password. The comparison does not establish equivalent security properties.

## Files

- `weighted_dte_results.json` and `weighted_dte_frequencies.csv`
- `weighted_dte_distribution.png`
- `side_information.json` and `side_information.png`
- `dictionary_attack.json`
