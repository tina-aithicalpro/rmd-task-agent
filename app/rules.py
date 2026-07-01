"""
RMD compliance and redaction rules - LOGIC, kept out of the database on purpose.
These mirror config/rmd_config.md from the weekly-update pipeline so the
standalone agent redacts IDENTICALLY to the pipeline. Divergence between the two
is a compliance risk, so this is the single source for the standalone side.

The API endpoints (this build) do not apply these yet. The draft generator
(next build) imports from here. Defined now so there is one place to change them.
"""

# --- Verified baseline (drift control) ---
AI_VISIBILITY_BASELINE = 36        # confirmed five-engine baseline
AI_VISIBILITY_TARGET = 90
RETIRED_SCORES = {18, 27}          # poisoned by 401 auth failures - never report

# --- Hard stops: never appears in any client-facing output ---
CLIENT_HARD_STOP_TERMS = {
    "botox",                       # RMD carries Dysport and Xeomin only
    "re-scope", "rescope", "change order", "goodwill pricing", "margin",
    "do not send", "scope-shrink", "conversion leak",
}

# Internal / third-party names that must never reach the client draft.
INTERNAL_NAMES = {
    "anuj", "erik", "tina", "ken baratsa", "ken", "darshan",
    "cameron", "jean", "ashish", "bob nascale", "automation email",
}

# Known directory/tool names from the RMD task set. These are MECHANICS - the
# client draft stays outcome-level and must never name them. Gate-enforced so a
# prompt slip fails closed rather than shipping.
MECHANIC_NAMES = {
    "webmd", "healthgrades", "realself", "zocdoc", "vitals.com", "vitals",
    "americanmedspa", "blotato", "showit", "reddit", "voyage raleigh",
    "google search console", "gsc", "indexing api", "faqpage schema",
    "sameas schema", "meta ad library",
}

# --- Prohibited vocabulary (stripped from all client copy) ---
PROHIBITED_VOCAB = {
    "streamline", "leverage", "unlock", "game-changer", "cutting-edge",
    "seamless", "robust", "synergy", "empower", "delve",
    "guarantee", "guaranteed", "eliminates", "cures", "treats", "heals",
    "fixes", "resolves",
}

# --- Cluster -> outcome transforms (client draft is OUTCOME level only) ---
# Maps external_ref clusters to a single client-safe outcome statement.
OUTCOME_TRANSFORMS = [
    (
        {"clickup-7", "clickup-8", "clickup-9", "clickup-10", "clickup-11", "clickup-12"},
        "Expanding your visibility across trusted medical directories.",
    ),
    (
        {"clickup-16", "clickup-17", "clickup-18", "clickup-19", "clickup-20", "clickup-28"},
        "Strengthening how your site answers common patient questions so it "
        "surfaces in AI and search results.",
    ),
    (
        {"clickup-22", "clickup-23", "clickup-24", "clickup-26", "clickup-30"},
        "Technical search-visibility work so your pages are correctly indexed.",
    ),
    (
        {"clickup-6", "clickup-13", "clickup-14", "clickup-32"},
        "Preparing press and editorial placements to build authority signals.",
    ),
    (
        {"clickup-1", "clickup-15"},
        "Keeping your reviews responded to and growing your review volume.",
    ),
]

# --- Required medical framing (when clinical/peptide work is described) ---
CREDENTIAL_LINE = (
    "the practice led by Dr. Bhavna Vaidya, MD, board certified, "
    "practicing since 2005"
)
REQUIRED_FRAMINGS = [
    "individual results vary",
    "under physician supervision",
]

# --- Routing header on every client draft ---
CLIENT_DRAFT_HEADER = (
    "STATUS: DRAFT - route to Jay for approval, then a team member sends to the "
    "RMD team. Do not send directly."
)


def contains_client_hard_stop(text: str) -> list[str]:
    """Return any hard-stop terms found in text (case-insensitive).
    Non-empty result means the text must NOT go to the client."""
    low = text.lower()
    banned = CLIENT_HARD_STOP_TERMS | INTERNAL_NAMES | MECHANIC_NAMES
    return [t for t in banned if t in low]
