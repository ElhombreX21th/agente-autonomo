"""Human-reviewed ticket triage using a small real offline Naive Bayes classifier.

Training examples are synthetic. Confidence is an uncalibrated model score, NOT
an estimate that the prediction is correct. This is a demo, not a safety system.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass
from math import exp, log
import re

CATEGORIES = ("connectivity", "hardware", "software", "data")
TRAINING = (
    ("connection timeouts after router reset network latency unreachable host", "connectivity"),
    ("wifi disconnects and cannot reach remote server", "connectivity"),
    ("tcp network socket connection refused from gateway", "connectivity"),
    ("sensor cable motor bearing component physically damaged", "hardware"),
    ("device power supply fan not spinning overheating", "hardware"),
    ("broken detector cable mechanical noise loose connector", "hardware"),
    ("application crashes after update exception stack trace", "software"),
    ("login page fails with software error and bug", "software"),
    ("program error after new firmware release regression", "software"),
    ("csv columns missing duplicate rows incorrect dataset", "data"),
    ("spreadsheet report totals mismatch records reconciliation", "data"),
    ("database export inconsistent fields and invalid data", "data"),
)

def _tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.lower())

@dataclass(frozen=True)
class Ticket:
    ticket_id: str
    title: str
    description: str
    operational_impact: str = "none"  # none | partial | stopped

class NaiveBayesClassifier:
    """Transparent multinomial text classifier trained only on demo examples."""
    def __init__(self, training=TRAINING):
        self.words = defaultdict(Counter)
        self.classes = Counter()
        self.vocabulary = set()
        for text, label in training:
            if label not in CATEGORIES:
                raise ValueError("Unknown category in training")
            tokens = _tokens(text)
            self.words[label].update(tokens)
            self.vocabulary.update(tokens)
            self.classes[label] += 1
        if not self.vocabulary:
            raise ValueError("Training data required")

    def predict(self, text: str) -> tuple[str, float]:
        tokens = _tokens(text)
        recognized = [t for t in tokens if t in self.vocabulary]
        if not recognized:
            return "data", 0.0
        scores = {}
        sample_count = sum(self.classes.values())
        for category in CATEGORIES:
            prior = log(self.classes[category] / sample_count)
            denominator = sum(self.words[category].values()) + len(self.vocabulary)
            scores[category] = prior + sum(
                log((self.words[category][word] + 1) / denominator)
                for word in recognized
            )
        top = max(scores, key=scores.get)
        normalizer = max(scores.values())
        exp_scores = {k: exp(v - normalizer) for k, v in scores.items()}
        confidence = exp_scores[top] / sum(exp_scores.values())
        return top, round(confidence, 4)

def triage(ticket: Ticket, model: NaiveBayesClassifier | None = None) -> dict:
    if not ticket.ticket_id.strip() or not ticket.title.strip():
        raise ValueError("ticket_id and title are required")
    if ticket.operational_impact not in {"none", "partial", "stopped"}:
        raise ValueError("operational_impact must be none, partial or stopped")
    model = model or NaiveBayesClassifier()
    category, model_score = model.predict(f"{ticket.title} {ticket.description}")
    priority = {"none": "P3", "partial": "P2", "stopped": "P1"}[ticket.operational_impact]
    human_review = ticket.operational_impact == "stopped" or model_score < 0.70
    return {
        "ticket_id": ticket.ticket_id,
        "category": category,
        "model_score_uncalibrated": model_score,
        "priority": priority,
        "human_review_required": human_review,
        "reason": (
            "Human review: critical operational impact or uncertain classifier output"
            if human_review else "Proposed routing; human override remains available"
        ),
        "status": "demonstration_only_not_auto_escalated",
    }
