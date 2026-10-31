import unittest
from upwork_showcase_2026.medtech_service_desk.logic import assess, ORDERS, dashboard as dispatch_dashboard
from upwork_showcase_2026.healthcare_data_quality.logic import reconcile, EXPECTED, reconcile_csv, dashboard as lab_dashboard
from upwork_showcase_2026.technical_presales_crm.logic import qualify, LEADS, dashboard as sales_dashboard

class WorkflowTests(unittest.TestCase):
    def test_dispatch_ready_is_not_auto_approved(self):
        self.assertEqual(assess(ORDERS[0])['status'], 'READY FOR MANUAL REVIEW')
    def test_dispatch_missing_access(self):
        self.assertTrue(any('access' in x.lower() for x in assess(ORDERS[1])['blockers']))
    def test_dispatch_missing_part(self):
        self.assertTrue(any('part' in x.lower() for x in assess(ORDERS[1])['blockers']))
    def test_dispatch_conflict(self):
        self.assertTrue(any('conflict' in x.lower() for x in assess(ORDERS[2])['blockers']))
    def test_dispatch_dashboard(self):
        self.assertEqual(dispatch_dashboard()['held'], 2)
    def test_lab_expected_missing(self):
        self.assertEqual(lab_dashboard()['summary']['missing'], 1)
    def test_lab_detects_mismatch(self):
        self.assertIn('PANEL_MISMATCH', lab_dashboard()['rule_counts'])
    def test_lab_duplicate(self):
        self.assertIn('DUPLICATE_SOURCE', lab_dashboard()['rule_counts'])
    def test_lab_schema_gate(self):
        with self.assertRaises(ValueError):
            reconcile_csv('patient_name,case_id,panel,status,source_id\nAlice,SIM-2101,CBC,FINAL,a\n')
    def test_lab_no_real_ids(self):
        with self.assertRaises(ValueError):
            reconcile_csv('case_id,panel,status,source_id\nAlice,CBC,FINAL,a\n')
    def test_lab_complete_data(self):
        data = [dict(case_id=x['case_id'], panel=x['expected_panel'],
                     status='FINAL', source_id='S'+str(i)) for i,x in enumerate(EXPECTED)]
        self.assertEqual(reconcile(EXPECTED, data)['summary']['exceptions'], 0)
    def test_sales_has_human_review(self):
        self.assertTrue(qualify(LEADS[0])['human_review_required'])
    def test_sales_qualifies(self):
        self.assertEqual(qualify(LEADS[0])['stage'], 'TECHNICAL REVIEW')
    def test_sales_consent_block(self):
        self.assertEqual(qualify(LEADS[2])['stage'], 'CONSENT REQUIRED')
    def test_sales_consent_no_due(self):
        self.assertIsNone(qualify(LEADS[2])['follow_up_due'])
    def test_sales_missing_budget(self):
        self.assertIn('Budget', qualify(LEADS[1])['missing'])
    def test_sales_dashboard(self):
        self.assertEqual(sales_dashboard()['total'], 4)

if __name__ == '__main__':
    unittest.main()
