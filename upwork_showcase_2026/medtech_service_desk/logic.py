"""Synthetic MedTech dispatch readiness checks; cannot authorize real dispatches."""
from datetime import datetime

ORDERS = [
    {"id": "WO-2048", "site": "North Harbor Imaging", "asset": "MR System / Demo-01", "type": "Preventive inspection", "priority": "Routine", "technician": "A. Martins", "date": "2026-11-03", "start": "09:00", "end": "11:00", "parts": ["Filter kit"], "stock": ["Filter kit"], "training": ["MR Safety", "Electrical LOTO"], "certs": ["MR Safety", "Electrical LOTO"], "induction": True, "access": True, "conflicts": [], "notes": "Scheduled maintenance window confirmed by site coordinator."},
    {"id": "WO-2049", "site": "Southside Diagnostics", "asset": "CT System / Demo-02", "type": "Cooling subsystem review", "priority": "High", "technician": "B. Ribeiro", "date": "2026-11-03", "start": "13:00", "end": "15:00", "parts": ["Pump assembly", "Seal kit"], "stock": ["Seal kit"], "training": ["CT Service"], "certs": ["CT Service"], "induction": True, "access": False, "conflicts": [], "notes": "Awaiting customer access permission and part restock."},
    {"id": "WO-2050", "site": "Metro Clinical Lab", "asset": "IVD Analyzer / Demo-03", "type": "Installation qualification", "priority": "Normal", "technician": "C. Santos", "date": "2026-11-04", "start": "10:00", "end": "12:00", "parts": ["IQ kit"], "stock": ["IQ kit"], "training": ["IVD Commissioning"], "certs": [], "induction": False, "access": True, "conflicts": ["Technician allocated at another site 10:30–11:30"], "notes": "Training and induction evidence must be resolved before approval."},
]

def assess(order: dict) -> dict:
    """Review readiness. 'ready' STILL requires human approval and is not a work order release."""
    blockers = []
    if not order.get('induction'):
        blockers.append('Site induction or visitor clearance missing')
    if not order.get('access'):
        blockers.append('Customer site access not authorized')
    for part in set(order.get('parts', [])) - set(order.get('stock', [])):
        blockers.append(f'Required part unavailable: {part}')
    for cert in set(order.get('training', [])) - set(order.get('certs', [])):
        blockers.append(f'Training evidence missing: {cert}')
    for conflict in order.get('conflicts', []):
        blockers.append(f'Schedule conflict: {conflict}')
    if not order.get('technician') or not order.get('site') or not order.get('asset'):
        blockers.append('Work order identity incomplete')
    try:
        if datetime.strptime(order['end'], '%H:%M') <= datetime.strptime(order['start'], '%H:%M'):
            blockers.append('Invalid service window')
    except (KeyError, ValueError, TypeError):
        blockers.append('Invalid appointment time')
    return {"id": order.get('id'), "ready": not blockers,
            "status": 'READY FOR MANUAL REVIEW' if not blockers else 'ON HOLD',
            "blockers": sorted(blockers),
            "next_step": 'Coordinator must confirm readiness and authorize dispatch' if not blockers else 'Resolve blockers, then rerun checks'}

def dashboard() -> dict:
    cases = [dict({k:v for k,v in order.items() if k not in ('stock','certs','conflicts')}, assessment=assess(order)) for order in ORDERS]
    return {"orders":cases, "total":len(cases), "ready":sum(x['assessment']['ready'] for x in cases),
            "held":sum(not x['assessment']['ready'] for x in cases),
            "checks":['Technician training', 'Site access', 'Induction clearance', 'Parts inventory', 'Schedule conflicts']}
