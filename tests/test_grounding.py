import unittest
from riskflow.ai import validate, STEPS


class GroundingTests(unittest.TestCase):
    def test_value_from_another_signal_cannot_be_reassigned(self):
        packet={'evidence':[{'id':'dti','value':.7,'threshold':.5,'points':20},
                            {'id':'late','value':35,'threshold':30,'points':40}]}
        response={'summary':'Review the flags.', 'observations':[{'evidence_id':'dti','explanation':'Observed 35.'}], 'next_steps':[STEPS[0]]}
        with self.assertRaises(ValueError):validate(response,packet)
        response['observations'][0]['explanation']='Observed 0.7.'
        self.assertEqual(validate(response,packet),response)
