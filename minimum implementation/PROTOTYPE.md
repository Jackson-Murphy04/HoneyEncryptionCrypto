# Prototype and evaluation guide

Python 3.10+ is required. Install dependencies with `python -m pip install -r requirements.txt`.

## Original uniform prototype

```bash
python honey.py messages
python honey.py encrypt "Meet me at library on Monday at 9am." demo.json
python honey.py decrypt demo.json
python -m unittest -v
python evaluate.py
```

The message set is 4 locations × 7 weekdays × 4 times = 112 sentences. The uniform DTE partitions the 256-bit seed space into 112 contiguous intervals. The password wrapper uses PBKDF2-HMAC-SHA256 (200,000 iterations), a 16-byte salt, and XOR. It intentionally has no password verifier or authentication tag. The CLI's example JSON includes the original plaintext and password as teaching metadata; this makes the record unsuitable for secure storage.

## Extensions

- `weighted_dte.py`: an integer-weight DTE using a synthetic product prior over location, day, and time. It is currently a standalone DTE component and is **not wired into the password wrapper**.
- `weighted_evaluate.py`: samples random 256-bit seeds and checks the weighted decoder against its declared target probabilities.
- `attacks.py`: calculates exact candidate-set reductions from known fields and runs a small synthetic password-rank pilot. The pilot's candidate list is not a representative human-password dataset and has no attacker correctness oracle.
- `baseline.py`: separate AES-256-GCM/scrypt authenticated-encryption comparison. A wrong password normally raises an authentication-tag failure; it does not generate decoys.

## Interpretation

A decoder always returning one of 112 strings demonstrates format validity only. It does not prove contextual plausibility, indistinguishability, or security. The weighted seed experiment checks only the weighted DTE component, not an end-to-end weighted HE scheme. The XOR/PBKDF2 prototype is educational and unauthenticated. Do not use it for real secrets.
