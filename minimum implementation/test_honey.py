"""Correctness checks for the bounded educational prototype."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import honey


class DistributionEncoderTests(unittest.TestCase):
    """Check every message and both ends of every seed interval."""

    def test_all_messages_and_boundaries(self):
        for index, message in enumerate(honey.MESSAGES):
            with self.subTest(message=message):
                self.assertEqual(honey.decode(honey.encode(message)), message)
                lower, upper = honey.seed_interval(index)
                for seed_number in (lower, upper - 1):
                    seed = seed_number.to_bytes(honey.SEED_BYTES, "big")
                    self.assertEqual(honey.decode(seed), message)


class EncryptionTests(unittest.TestCase):
    """Check recovery, repeatable guesses, and fresh encryption randomness."""

    def test_password_recovery_and_randomness(self):
        message = honey.MESSAGES[0]
        record = honey.encrypt(message, "correct")
        self.assertEqual(honey.decrypt(record, "correct"), message)

        wrong_output = honey.decrypt(record, "wrong")
        self.assertIn(wrong_output, honey.MESSAGES)
        self.assertEqual(wrong_output, honey.decrypt(record, "wrong"))
        self.assertNotEqual(record, honey.encrypt(message, "correct"))

    def test_metadata_is_saved_but_not_used_for_decryption(self):
        message = honey.MESSAGES[0]
        record = honey.encrypt(message, "demo")
        self.assertEqual(
            record["example"],
            {"original_message": message, "original_password": "demo"},
        )

        # Simulate a JSON round trip and replace the stored teaching answer.
        restored = json.loads(json.dumps(record))
        restored["example"] = {
            "original_message": "ignored",
            "original_password": "ignored",
        }
        self.assertEqual(honey.decrypt(restored, "demo"), message)

        # Files created before teaching metadata was added remain readable.
        del restored["example"]
        self.assertEqual(honey.decrypt(restored, "demo"), message)


class ExampleFileTests(unittest.TestCase):
    """Verify folder placement, JSON round trips, and overwrite protection."""

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            examples = Path(temporary_directory) / "examples"
            with patch.object(honey, "EXAMPLES_DIRECTORY", examples):
                record = honey.encrypt(honey.MESSAGES[0], "demo")
                saved_path = honey.save_example(record, Path("demo.json"))
                self.assertEqual(saved_path, examples / "demo.json")
                self.assertEqual(honey.load_example(saved_path), record)
                self.assertEqual(honey.load_example(Path("demo.json")), record)
                with self.assertRaises(FileExistsError):
                    honey.save_example(record, Path("demo.json"))


if __name__ == "__main__":
    unittest.main()
