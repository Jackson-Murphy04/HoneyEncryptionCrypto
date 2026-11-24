import unittest
import honey
import weighted_dte
from attacks import feature

class WeightedDTETests(unittest.TestCase):
    def test_intervals_partition_seed_space(self):
        bounds=[weighted_dte.interval(i) for i in range(honey.MESSAGE_COUNT)]
        self.assertEqual(bounds[0][0],0)
        self.assertEqual(bounds[-1][1],honey.SEED_SPACE)
        for i,(lo,hi) in enumerate(bounds):
            self.assertLess(lo,hi)
            self.assertEqual(weighted_dte.decode(lo.to_bytes(honey.SEED_BYTES,'big')),honey.MESSAGES[i])
            self.assertEqual(weighted_dte.decode((hi-1).to_bytes(honey.SEED_BYTES,'big')),honey.MESSAGES[i])
            if i: self.assertEqual(bounds[i-1][1],lo)
    def test_round_trip_all_messages(self):
        for m in honey.MESSAGES:
            self.assertEqual(weighted_dte.decode(weighted_dte.encode(m)),m)
    def test_nonuniform_prior(self):
        probs=weighted_dte.target_probabilities()
        self.assertAlmostEqual(sum(probs),1.0)
        self.assertGreater(max(probs),min(probs))

class SideInfoTests(unittest.TestCase):
    def test_feature_parser(self):
        m='Meet me at library on Monday at 9am.'
        self.assertEqual(feature(m,'location'),'library')
        self.assertEqual(feature(m,'day'),'Monday')
        self.assertEqual(feature(m,'time'),'9am')

if __name__=='__main__': unittest.main()
