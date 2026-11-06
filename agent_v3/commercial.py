"""Entitlement and billing boundaries; no live checkout or payment side effects."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Entitlements:
    plan: str
    max_stored_tasks: int
    billing_active: bool = False


PILOT = Entitlements("pilot", 1000)
PRICING_HYPOTHESES_BRL = {
    "starter": 99,
    "professional": 299,
    "business": 999,
    "enterprise": None,
}


class BillingProvider(Protocol):
    def status(self, workspace: str) -> dict: ...


class DisabledBilling:
    def status(self, workspace: str) -> dict:
        return {
            "provider": "disabled",
            "active_subscription": False,
            "charges_enabled": False,
        }

    def checkout(self, workspace: str):
        raise PermissionError(
            "Live billing is disabled; commercial authorization and integration required"
        )
