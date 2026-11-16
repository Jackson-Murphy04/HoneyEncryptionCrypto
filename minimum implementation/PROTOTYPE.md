# Python CLI prototype
Python 3.10+, standard library only. From this directory:

    python honey.py messages
    python honey.py encrypt "Meet me at library on Monday at 9am." example.json
    python honey.py decrypt example.json
    python -m unittest -v

Passwords are prompted without echo. Each new example JSON file includes an example object with original_message and original_password in plain text for classroom comparison. Use demo passwords only. Output files must not already exist. Decryption ignores the example metadata and still uses the password you enter; older files without metadata also work. Existing examples cannot have their original password recovered automatically.
Wrong passwords yield deterministic supported sentences, potentially the original by chance.

The model has 112 uniform messages. A randomized DTE uses contiguous intervals
covering all 256-bit seeds; interval sizes differ by at most one. Decoding is total.
A fresh 16-byte salt and PBKDF2-HMAC-SHA256 with 200,000 iterations derive a
32-byte mask, XORed with the seed. No password verifier or authentication tag is
stored in the cryptographic payload. The educational example metadata explicitly discloses the password and message, so these files provide no secrecy. Public format errors are independent of password correctness.

This provisional educational construction still needs the README's research and
design review. It provides no integrity protection or demonstrated security.
Research, formal distribution evaluation, and the paper remain open.
AI assistance: Codex generated the implementation, tests and these notes.


Example files are always created in the examples folder beside honey.py.
The encrypt argument supplies the filename (any directory portion is ignored).
The saved absolute path is printed. For example:

    python honey.py encrypt "Meet me at library on Monday at 9am." demo.json
    python honey.py decrypt examples/demo.json

Decryption also accepts a bare filename such as demo.json and checks examples
if that file is not in the current directory.

## Implementation layout
Run the commands above from the minimum implementation folder:

    cd "C:\Users\Jackson\Desktop\Honey Encryption\minimum implementation"

honey.py is organized into message parameters, DTE, password masking,
example file handling, and CLI sections. test_honey.py groups checks by behavior.
The examples folder contains the saved classroom records.
