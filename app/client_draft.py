"""
Client-draft generator. Claude writes the draft (natural, outcome-level), then a
self-check gate scans the output and REFUSES to return it if it contains any
hard-stop term, internal name, or prohibited word. Fails closed: a compliance
leak blocks the response rather than shipping.

The draft is returned to an authenticated caller and routed into the human
approval chain (team -> Jay -> send). It is never parked at a public URL.
"""
from datetime import datetime, timedelta, timezone
import anthropic

from . import db
from .settings import settings
from .rules import (
    PROHIBITED_VOCAB, CLIENT_HARD_STOP_TERMS, INTERNAL_NAMES, MECHANIC_NAMES,
    CREDENTIAL_LINE, CLIENT_DRAFT_HEADER, contains_client_hard_stop,
)


class ComplianceBlock(Exception):
    """Raised when the generated draft fails the self-check gate."""


def _scrub(text: str) -> str:
    """Remove any internal name from text before it reaches the prompt. Titles
    can contain internal names (e.g. 'Connect with Ken Baratsa'), so we strip
    them at the source rather than trust the title is clean. Belt to the gate's
    suspenders: never feed a name in, and catch it if one slips."""
    if not text:
        return text
    out = text
    for name in sorted(INTERNAL_NAMES, key=len, reverse=True):
        # case-insensitive removal
        idx = out.lower().find(name.lower())
        while idx != -1:
            out = out[:idx] + out[idx + len(name):]
            idx = out.lower().find(name.lower())
    # tidy leftover artifacts from removed names
    out = out.replace("(, ", "(").replace(", )", ")").replace("()", "")
    out = " ".join(out.split())
    return out.strip(" ,-")


def _gather_client_visible():
    """Only statuses the client may see: completed, in_progress, on_hold_client.
    on_hold_internal and internal_blocked details are excluded here."""
    week_start = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    completed = db.completed_since(week_start)
    ongoing = db.list_tasks(status="in_progress")
    awaiting_client = db.list_tasks(status="on_hold_client")
    # strip internal-only fields AND scrub internal names from titles before the prompt
    def clean(t):
        return {"ref": t["external_ref"], "title": _scrub(t["title"]), "workstream": t["workstream"]}
    return (
        [clean(t) for t in completed],
        [clean(t) for t in ongoing],
        # awaiting-client: client needs to know WHAT decision is needed, phrased
        # from the title only. blocker_note is internal routing metadata (may name
        # staff) and must NOT reach the prompt. Title only.
        [{"title": _scrub(t["title"])} for t in awaiting_client],
    )


def _build_prompt(completed, ongoing, awaiting):
    return f"""You are drafting a weekly client update for RegenesisMD, a medical practice.
Write it warm, plain, and OUTCOME-LEVEL. This is the hard rule: describe outcomes
and benefits, NEVER individual task titles, tool names, directory names (WebMD,
Zocdoc, etc.), or step mechanics. Group related work into outcome statements.

Absolute rules:
- No em dashes. Use a spaced hyphen if needed.
- Never use: streamline, leverage, unlock, game-changer, cutting-edge, seamless,
  robust, synergy, empower, delve, guarantee, cures, treats, heals, fixes, eliminates.
- Never write "Botox". Never name any staff, vendor, or internal person.
- Where clinical or peptide work is described, include "individual results vary"
  and physician-supervision framing.
- End the sign-off referencing: {CREDENTIAL_LINE}.

Structure exactly three sections:
1. "Completed this week" - if the list is empty, say so honestly, do not invent.
2. "Ongoing work" - outcome level.
3. "Waiting on your input" - only the items below, phrased as simple asks.

COMPLETED (raw, transform to outcomes): {completed}
ONGOING (raw, transform to outcomes): {ongoing}
AWAITING CLIENT INPUT (phrase as asks): {awaiting}

Return only the body text of the update, no preamble."""


def _self_check(text: str) -> list[str]:
    """Scan generated text. Return list of violations. Empty = passes."""
    low = text.lower()
    hits = []
    hits += [t for t in (CLIENT_HARD_STOP_TERMS | INTERNAL_NAMES | MECHANIC_NAMES) if t in low]
    hits += [w for w in PROHIBITED_VOCAB if w in low.split() or w in low]
    if "\u2014" in text or "\u2013" in text:  # em dash / en dash
        hits.append("em-or-en-dash")
    return sorted(set(hits))


def generate_client_draft() -> dict:
    completed, ongoing, awaiting = _gather_client_visible()

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        messages=[{"role": "user", "content": _build_prompt(completed, ongoing, awaiting)}],
    )
    body = "".join(b.text for b in msg.content if b.type == "text").strip()

    violations = _self_check(body)
    if violations:
        # fail closed - do not return draft text that violated the gate
        raise ComplianceBlock(
            "Draft blocked by self-check. Violations: " + ", ".join(violations)
            + ". Regenerate or review manually. Draft NOT returned."
        )

    full = f"{CLIENT_DRAFT_HEADER}\n\nWeek of: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\nTo: Dr. Vaidya and the RegenesisMD team\nFrom: Your Aithical team\n\n{body}"
    return {"status": "draft_ready", "routing": "team -> Jay approval -> send", "draft": full}
