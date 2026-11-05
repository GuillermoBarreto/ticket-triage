"""Transparent rule-based ticket triage.

No model, no network, no paid API: every decision is a keyword score
the caller can inspect. Scores, matched keywords, and routing are all
returned alongside the category so a human can audit the result.

All tickets handled here are synthetic samples. Never feed real work
tickets, customer data, or anything resembling a real job ticket into
this tool.
"""

import re

CATEGORIES = ("network", "hardware", "access", "software", "other")

# Ties are broken deterministically by this order (first wins).
PRIORITY = ("network", "hardware", "access", "software")

KEYWORDS = {
    "network": [
        "wifi", "wi-fi", "vpn", "internet", "network", "networking",
        "router", "switch", "ethernet", "dns", "latency", "bandwidth",
        "connection", "connectivity", "offline", "dropout", "drops",
        "dropping",
    ],
    "hardware": [
        "laptop", "monitor", "printer", "keyboard", "mouse", "battery",
        "screen", "power", "boot", "fan", "dock", "docking", "cable",
        "flicker", "flickering", "hardware",
    ],
    "access": [
        "password", "passwords", "login", "log in", "locked out",
        "access", "permission", "permissions", "account", "mfa",
        "two-factor", "reset", "credentials", "sign in", "sign-in",
    ],
    "software": [
        "crash", "crashes", "crashing", "error", "bug", "app",
        "application", "update", "install", "software", "freeze",
        "freezes", "freezing", "save", "saving",
    ],
}

ROUTING = {
    "network": "Network Operations",
    "hardware": "Hardware Support",
    "access": "Identity & Access Management",
    "software": "Application Support",
    "other": "General IT Triage",
}

NEXT_STEPS = {
    "network": "The network team will check connectivity and follow up with diagnostics.",
    "hardware": "The hardware team will arrange inspection or a replacement.",
    "access": "The access team will verify identity and restore access.",
    "software": "The application team will reproduce the issue and advise on a workaround.",
    "other": "A triage agent will review this and assign it to the right team.",
}


def _matched_keywords(text, keywords):
    """Return the keywords found in text, using word boundaries.

    Multi-word keywords (e.g. "locked out") match as phrases. Matching
    is case-insensitive. A keyword only counts once, no matter how
    often it appears, so repeating one word cannot dominate the score.
    """
    lowered = text.lower()
    found = []
    for keyword in keywords:
        pattern = r"\b" + re.escape(keyword) + r"\b"
        if re.search(pattern, lowered):
            found.append(keyword)
    return found


def score_ticket(title, description):
    """Score a ticket against every category.

    Returns a dict of category -> {"score": int, "matched": [keywords]}.
    The "other" category never scores; it is the fallback when nothing
    matches.
    """
    text = "{} {}".format(title, description)
    scores = {}
    for category in PRIORITY:
        matched = _matched_keywords(text, KEYWORDS[category])
        scores[category] = {"score": len(matched), "matched": matched}
    scores["other"] = {"score": 0, "matched": []}
    return scores


def confidence_for(scores):
    """Label how clear-cut a triage call is, for a human reviewer.

    Returns (label, note). No matches means low confidence; a tie for
    first place is a close call to double-check; a lead of two or more
    over the runner-up is high confidence; anything else is medium.
    """
    ranked = sorted(
        (info["score"] for info in scores.values() if info["score"] > 0),
        reverse=True,
    )
    if not ranked:
        return "low", "No keyword matches — needs human review."
    if len(ranked) > 1 and ranked[0] == ranked[1]:
        return "low", "Close call — top categories tied; double-check before routing."
    if len(ranked) == 1 or ranked[0] - ranked[1] >= 2:
        return "high", "Clear lead over the next category."
    return "medium", "Narrow lead over the next category."


def triage(title, description, reporter="Reporter"):
    """Triage one ticket and build its draft reply.

    Returns a dict with category, per-category scores, matched
    keywords, suggested routing, confidence, and a draft reply. The
    draft is for a human agent to review before sending; nothing is
    sent anywhere.
    """
    scores = score_ticket(title, description)
    best = "other"
    best_score = 0
    for category in PRIORITY:
        if scores[category]["score"] > best_score:
            best = category
            best_score = scores[category]["score"]
    route = ROUTING[best]
    confidence, confidence_note = confidence_for(scores)
    reply = (
        "Hi {},\n\n"
        "Thanks for reporting \"{}\". We've triaged this as {} "
        "and routed it to {}.\n"
        "{}\n\n"
        "This is a draft for a human agent to review before sending."
    ).format(reporter, title, best, route, NEXT_STEPS[best])
    return {
        "category": best,
        "scores": scores,
        "routing": route,
        "confidence": confidence,
        "confidence_note": confidence_note,
        "draft_reply": reply,
    }


def batch_triage(tickets):
    """Triage a list of ticket dicts (title, description, reporter, id).

    Returns one result dict per ticket, preserving its id when given.
    Raises ValueError if the input is not a list or a ticket lacks a
    title or description, so a malformed batch fails loudly instead
    of silently triaging partial data.
    """
    if not isinstance(tickets, list):
        raise ValueError("batch input must be a JSON list of tickets")
    results = []
    for ticket in tickets:
        if not isinstance(ticket, dict):
            raise ValueError("each ticket must be an object")
        if "title" not in ticket or "description" not in ticket:
            raise ValueError("each ticket needs a title and a description")
        result = triage(
            ticket["title"],
            ticket["description"],
            reporter=ticket.get("reporter", "Reporter"),
        )
        results.append({
            "id": ticket.get("id"),
            "title": ticket["title"],
            "category": result["category"],
            "routing": result["routing"],
            "confidence": result["confidence"],
            "confidence_note": result["confidence_note"],
            "scores": result["scores"],
            "draft_reply": result["draft_reply"],
        })
    return results
