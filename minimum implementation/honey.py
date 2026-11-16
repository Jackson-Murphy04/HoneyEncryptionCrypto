"""Minimal educational honey encryption over a fixed set of English messages.

The example metadata deliberately records the password and plaintext. This is a
teaching prototype, with no secrecy or integrity guarantee for its saved files.
"""

import argparse
import getpass
import hashlib
import json
import secrets
from pathlib import Path


# ---------------------------------------------------------------------------
# Message model and public parameters
# ---------------------------------------------------------------------------
# Ordering is part of the format: changing these tuples changes seed decoding.
LOCATIONS = ("library", "cafe", "park", "office")
DAYS = (
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
)
TIMES = ("9am", "12pm", "3pm", "6pm")

MESSAGES = tuple(
    f"Meet me at {location} on {day} at {time}."
    for location in LOCATIONS
    for day in DAYS
    for time in TIMES
)
MESSAGE_COUNT = len(MESSAGES)
SEED_BYTES = 32
SEED_SPACE = 1 << (8 * SEED_BYTES)
SALT_BYTES = 16
PBKDF2_ITERATIONS = 200_000
FORMAT_VERSION = 1
EXAMPLES_DIRECTORY = Path(__file__).resolve().parent / "examples"


# ---------------------------------------------------------------------------
# Distribution-transforming encoder (DTE)
# ---------------------------------------------------------------------------
def seed_interval(message_index: int) -> tuple[int, int]:
    """Return this message's inclusive lower and exclusive upper seed bounds."""
    if not 0 <= message_index < MESSAGE_COUNT:
        raise ValueError("Message index is outside the supported model.")

    # Ceiling division partitions every integer in [0, SEED_SPACE).
    # The intervals differ in size by at most one, giving negligible bias
    # relative to the intended uniform distribution of messages.
    lower = (message_index * SEED_SPACE + MESSAGE_COUNT - 1) // MESSAGE_COUNT
    upper = ((message_index + 1) * SEED_SPACE + MESSAGE_COUNT - 1) // MESSAGE_COUNT
    return lower, upper


def encode(message: str) -> bytes:
    """Randomly encode a supported sentence as one of its assigned seeds."""
    try:
        message_index = MESSAGES.index(message)
    except ValueError:
        raise ValueError("Unsupported sentence; run 'messages' for valid text.") from None

    lower, upper = seed_interval(message_index)
    seed_number = lower + secrets.randbelow(upper - lower)
    return seed_number.to_bytes(SEED_BYTES, "big")


def decode(seed: bytes) -> str:
    """Deterministically map every correctly sized seed to a supported sentence."""
    if len(seed) != SEED_BYTES:
        raise ValueError(f"Seed must be {SEED_BYTES} bytes.")

    seed_number = int.from_bytes(seed, "big")
    message_index = seed_number * MESSAGE_COUNT // SEED_SPACE
    return MESSAGES[message_index]


# ---------------------------------------------------------------------------
# Password mask and example record
# ---------------------------------------------------------------------------
def apply_password_mask(seed: bytes, password: str, salt: bytes) -> bytes:
    """XOR a seed with a password-derived mask; applying it twice recovers it."""
    mask = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=SEED_BYTES,
    )
    return bytes(seed_byte ^ mask_byte for seed_byte, mask_byte in zip(seed, mask))


def encrypt(message: str, password: str) -> dict:
    """Create a randomized encrypted seed plus explicit teaching metadata."""
    seed = encode(message)
    salt = secrets.token_bytes(SALT_BYTES)
    ciphertext = apply_password_mask(seed, password, salt)

    return {
        "version": FORMAT_VERSION,
        "salt": salt.hex(),
        "ciphertext": ciphertext.hex(),
        "example": {
            "original_message": message,
            "original_password": password,
        },
    }


def decrypt(record: dict, password: str) -> str:
    """Decode a password guess without consulting the example's stored answer."""
    required_fields = {"version", "salt", "ciphertext"}
    allowed_fields = (required_fields, required_fields | {"example"})
    if (
        not isinstance(record, dict)
        or set(record) not in allowed_fields
        or type(record["version"]) is not int
        or record["version"] != FORMAT_VERSION
    ):
        raise ValueError("Invalid or unsupported example format.")

    try:
        salt = bytes.fromhex(record["salt"])
        ciphertext = bytes.fromhex(record["ciphertext"])
    except (TypeError, ValueError):
        raise ValueError("Salt and ciphertext must be hexadecimal strings.") from None

    if len(salt) != SALT_BYTES or len(ciphertext) != SEED_BYTES:
        raise ValueError("Invalid salt or ciphertext length.")

    # There is intentionally no password authentication check. Any password
    # produces a seed, and every seed decodes to a sentence in the model.
    seed = apply_password_mask(ciphertext, password, salt)
    return decode(seed)


# ---------------------------------------------------------------------------
# Example file handling
# ---------------------------------------------------------------------------
def save_example(record: dict, filename: Path) -> Path:
    """Save inside the implementation's examples folder without overwriting."""
    EXAMPLES_DIRECTORY.mkdir(exist_ok=True)
    output_path = EXAMPLES_DIRECTORY / filename.name
    with output_path.open("x", encoding="utf-8") as example_file:
        json.dump(record, example_file, indent=2)
        example_file.write("\n")
    return output_path


def load_example(filename: Path) -> dict:
    """Read an explicit path, or look for a bare filename in examples."""
    input_path = filename
    if not input_path.is_file() and filename == Path(filename.name):
        input_path = EXAMPLES_DIRECTORY / filename.name
    return json.loads(input_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """Describe the three supported commands and their arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("messages", help="List every supported sentence.")

    encrypt_parser = commands.add_parser("encrypt", help="Create an example file.")
    encrypt_parser.add_argument("message", help="An exact supported sentence.")
    encrypt_parser.add_argument("file", type=Path, help="Filename within examples.")

    decrypt_parser = commands.add_parser("decrypt", help="Try a password guess.")
    decrypt_parser.add_argument("file", type=Path, help="Example filename or path.")
    return parser


def main() -> None:
    """Dispatch commands and report input errors without a Python traceback."""
    parser = build_parser()
    arguments = parser.parse_args()

    try:
        if arguments.command == "messages":
            print("\n".join(MESSAGES))
        elif arguments.command == "encrypt":
            # Validate before asking the user to enter a password.
            if arguments.message not in MESSAGES:
                raise ValueError("Unsupported sentence; run 'messages' for valid text.")
            password = getpass.getpass("Password: ")
            if not password:
                raise ValueError("Password must not be empty.")
            record = encrypt(arguments.message, password)
            output_path = save_example(record, arguments.file)
            print(f"Saved {output_path}")
        else:
            record = load_example(arguments.file)
            password = getpass.getpass("Password: ")
            print(decrypt(record, password))
    except (ValueError, TypeError, KeyError, OSError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
