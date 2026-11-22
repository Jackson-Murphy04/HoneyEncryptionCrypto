# Python CLI prototype and evaluation

Python 3.10+ is required. The prototype uses the standard library. The evaluation script requires the packages in `requirements.txt`.

## Commands

From this directory:

```bash
python honey.py messages
python honey.py encrypt "Meet me at library on Monday at 9am." example.json
python honey.py decrypt example.json
python -m unittest -v
python evaluate.py
```

Passwords are prompted without echo. The CLI's JSON example record includes the original message and password in plaintext as teaching metadata. Decryption ignores that metadata. Use demo passwords only; the files are not secure storage. Output files must not already exist.

## Message model and DTE

There are 4 locations × 7 days × 4 times = 112 equally weighted messages. Each message receives a contiguous interval in the 256-bit seed space. The encoder samples uniformly from the selected interval; the decoder maps every 32-byte seed to one sentence. Interval sizes differ by at most one because 112 does not evenly divide the seed space.

## Password layer

A 16-byte salt and PBKDF2-HMAC-SHA256 with 200,000 iterations derive a 32-byte mask. Encryption XORs this mask with the DTE seed; decryption XORs it again. No password verifier or authentication tag is present. Any password guess yields a supported sentence. This is an educational construction, not a reviewed production honey-encryption implementation.

## Evaluation

`evaluate.py` runs two separate experiments: (1) decoding uniformly sampled 256-bit seeds, and (2) decrypting one fixed ciphertext/salt using distinct random incorrect passwords. It records per-message frequencies, Pearson chi-square statistics, p-values, total variation distance, standardized residuals, and runtime. It writes JSON, CSV, Markdown, and PNG outputs to `evaluation_results/` by default. See the top-level README and the generated `evaluation_results/RESULTS.md` for measured results and caveats.

The wrong-password experiment uses random high-entropy candidate passwords, not a human password distribution or a dictionary attack. A large chi-square p-value is not proof of uniformity or security. Every decoded output being a valid member of the bounded message set is guaranteed by the decoder and is not evidence of semantic plausibility.
