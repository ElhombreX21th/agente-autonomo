"""Technical pre-sales qualification; no emails, no real customer data, no CRM writes."""
from datetime import date, timedelta

LEADS = [
    {'id':'OPP-104','company':'Aster Diagnostics','sector':'Diagnostics','product':'Service analytics portal','use_case':'Standardize service status across multiple sites','decision_maker':True,'budget':True,'timeline_days':45,'constraints':True,'consent':True,'value':12500,'owner':'F. Cruz'},
    {'id':'OPP-105','company':'Atlas Imaging Group','sector':'Medical imaging','product':'Asset monitoring integration','use_case':'Connect existing asset records to reporting','decision_maker':False,'budget':False,'timeline_days':90,'constraints':False,'consent':True,'value':7800,'owner':'F. Cruz'},
    {'id':'OPP-106','company':'Northpoint Labs','sector':'Laboratory','product':'Workflow automation','use_case':'Reduce duplicate intake handling','decision_maker':True,'budget':True,'timeline_days':30,'constraints':True,'consent':False,'value':9200,'owner':'F. Cruz'},
    {'id':'OPP-107','company':'Evergreen Devices','sector':'Medical devices','product':'Technical service workflow','use_case':'Coordinate service handoffs between regions','decision_maker':True,'budget':False,'timeline_days':None,'constraints':True,'consent':True,'value':6000,'owner':'F. Cruz'},
]

def qualify(lead:dict,today:date=date(2026,10,31))->dict:
    rules={'Use case':bool(lead.get('use_case')),'Decision maker':bool(lead.get('decision_maker')),
           'Budget':bool(lead.get('budget')),'Timeline':isinstance(lead.get('timeline_days'),int) and lead['timeline_days']>=0,
           'Integration fit':bool(lead.get('constraints'))}
    score=sum(rules.values())
    missing=[k for k,v in rules.items() if not v]
    if not lead.get('consent'):
        stage='CONSENT REQUIRED';action='Do not initiate outreach until contact permission is documented';due=None
    elif score>=4:
        stage='TECHNICAL REVIEW';action='Propose technical discovery with an authorized sales owner';due=(today+timedelta(days=1)).isoformat()
    else:
        stage='QUALIFICATION';action='Clarify '+', '.join(missing);due=(today+timedelta(days=3)).isoformat()
    return {'id':lead.get('id'),'score':score,'max_score':5,'checks':rules,'missing':missing,'stage':stage,
            'next_action':action,'follow_up_due':due,'human_review_required':True}

def dashboard():
    records=[{**lead,'qualification':qualify(lead)} for lead in LEADS]
    return {'leads':records,'total':len(records),'qualified':sum(l['qualification']['score']>=4 and l['consent'] for l in records),
            'needs_discovery':sum(l['qualification']['stage']=='QUALIFICATION' for l in records),
            'blocked':sum(not l['consent'] for l in records),
            'potential_value_demo':sum(l['value'] for l in records)}
