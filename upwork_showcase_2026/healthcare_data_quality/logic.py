"""Synthetic laboratory record reconciliation. No PHI and no clinical interpretation."""
from collections import Counter
import csv
import io

EXPECTED = [
    {'case_id':'SIM-2101','expected_panel':'CBC'}, {'case_id':'SIM-2102','expected_panel':'GLU'},
    {'case_id':'SIM-2103','expected_panel':'LIPID'}, {'case_id':'SIM-2104','expected_panel':'CBC'},
    {'case_id':'SIM-2105','expected_panel':'GLU'}, {'case_id':'SIM-2106','expected_panel':'LIPID'},
    {'case_id':'SIM-2107','expected_panel':'CBC'}, {'case_id':'SIM-2108','expected_panel':'GLU'}]
REPORTS = [
    {'case_id':'SIM-2101','panel':'CBC','status':'FINAL','source_id':'SRC-001'},
    {'case_id':'SIM-2102','panel':'GLU','status':'FINAL','source_id':'SRC-002'},
    {'case_id':'SIM-2103','panel':'CBC','status':'FINAL','source_id':'SRC-003'},
    {'case_id':'SIM-2104','panel':'CBC','status':'PENDING','source_id':'SRC-004'},
    {'case_id':'SIM-2105','panel':'GLU','status':'FINAL','source_id':'SRC-002'},
    {'case_id':'SIM-2106','panel':'LIPID','status':'FINAL','source_id':'SRC-006'},
    {'case_id':'SIM-2107','panel':'CBC','status':'FINAL','source_id':'SRC-007'},
]

def reconcile(expected: list[dict], received: list[dict]) -> dict:
    expected_map = {}
    issues=[]
    for row in expected:
        case=row.get('case_id','')
        if not case.startswith('SIM-') or not row.get('expected_panel'):
            issues.append({'case_id':case,'rule':'INVALID_EXPECTED','detail':'Invalid synthetic inventory row'})
        elif case in expected_map:
            issues.append({'case_id':case,'rule':'DUPLICATE_CASE','detail':'Duplicate inventory reference'})
        else:
            expected_map[case]=row['expected_panel']
    seen_sources=set()
    accepted=set()
    results=[]
    for row in received:
        case=row.get('case_id','')
        reason=[]
        src=row.get('source_id','')
        if case not in expected_map:reason.append('UNKNOWN_CASE')
        if not src or src in seen_sources:reason.append('DUPLICATE_SOURCE')
        else: seen_sources.add(src)
        if case in expected_map and row.get('panel')!=expected_map[case]: reason.append('PANEL_MISMATCH')
        if row.get('status') not in ('FINAL','PENDING'):reason.append('INVALID_STATUS')
        if case in accepted:reason.append('DUPLICATE_REPORT')
        if reason:
            for why in reason:issues.append({'case_id':case,'rule':why,'detail': 'Source '+src})
        else:accepted.add(case)
        results.append({**row,'result':'FLAGGED' if reason else 'PASS','rules':reason})
    for case in sorted(set(expected_map)-set(row.get('case_id') for row in received)):
        issues.append({'case_id':case,'rule':'MISSING_REPORT','detail':'No report received'})
    return {'summary':{'expected':len(expected),'received':len(received),'passed':sum(x['result']=='PASS' for x in results),'flagged':len([r for r in results if r['result']=='FLAGGED']), 'missing':sum(i['rule']=='MISSING_REPORT' for i in issues),'exceptions':len(issues)},
            'rows':results,'exceptions':issues,'rule_counts':dict(Counter(x['rule'] for x in issues)),
            'disclaimer':'All references are fictional; never process real patient data in this demo.'}

def dashboard():return reconcile(EXPECTED,REPORTS)

def reconcile_csv(csv_text: str) -> dict:
    if len(csv_text)>100_000:raise ValueError('Input too large for demo')
    reader=csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames!=['case_id','panel','status','source_id']:
        raise ValueError('CSV header must be: case_id,panel,status,source_id; no identifying columns permitted')
    rows=list(reader)
    if len(rows)>500:raise ValueError('Limit is 500 synthetic rows')
    if any(not str(r.get('case_id','')).startswith('SIM-') for r in rows):
        raise ValueError('Only SIM- synthetic IDs are allowed')
    return reconcile(EXPECTED,rows)
