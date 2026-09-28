"""Mechanical checks of the spend stop and paired bootstrap, without inference."""
import importlib.util, os, tempfile, unittest
from pathlib import Path
from summarize import bootstrap
class ProtocolTests(unittest.TestCase):
 def test_bootstrap_keeps_zero_and_positive_differences(self):
  self.assertEqual(bootstrap([0]*8),[0,0])
  for bound in bootstrap([.2]*8):self.assertAlmostEqual(bound,.2)
 def test_bootstrap_is_independent_of_result_file_order(self):
  self.assertEqual(bootstrap([.8,-.2,0,.4]),bootstrap([0,.4,.8,-.2]))
 def test_budget_reserves_unknown_cost_and_stops(self):
  with tempfile.TemporaryDirectory() as d:
   os.environ['LAB_STATE']=d
   spec=importlib.util.spec_from_file_location('gateway',Path(__file__).with_name('gateway.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
   g.CAP=.1
   g.reserve('a');g.reserve('b')
   with self.assertRaisesRegex(ValueError,'BUDGET_LIMIT'):g.reserve('c')
   with g.connection() as c:c.execute("update calls set state='done',cost=.001,input=2,output=3 where run='a'")
   g.reserve('c')
   with self.assertRaisesRegex(ValueError,'BUDGET_LIMIT'):g.reserve('d')
 def test_retry_shares_primary_inference_budget(self):
  with tempfile.TemporaryDirectory() as d:
   os.environ['LAB_STATE']=d
   spec=importlib.util.spec_from_file_location('gateway',Path(__file__).with_name('gateway.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
   g.reserve('primary')
   with g.connection() as c:
    c.execute('insert into budget_groups values(?,?,?)',('paired',100000,20))
    c.executemany('insert into budget_members values(?,?)',[('primary','paired'),('retry','paired')])
    c.execute("update calls set state='done',cost=.01,input=99999,output=1 where run='primary'")
   with self.assertRaisesRegex(ValueError,'BUDGET_LIMIT'):g.reserve('retry')
if __name__=='__main__':unittest.main()
