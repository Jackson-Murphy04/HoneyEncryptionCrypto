import unittest
import baseline
from cryptography.exceptions import InvalidTag

class AuthenticatedBaselineTests(unittest.TestCase):
    def test_round_trip(self):
        r=baseline.encrypt('Meet me at library on Monday at 9am.','test password')
        self.assertEqual(baseline.decrypt(r,'test password'),'Meet me at library on Monday at 9am.')
    def test_wrong_password_fails_authentication(self):
        r=baseline.encrypt('secret message','test password')
        with self.assertRaises(InvalidTag): baseline.decrypt(r,'wrong password')

if __name__=='__main__': unittest.main()
