from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Article:
    id: str
    title: str
    content: str


@dataclass(frozen=True)
class HeldOutQuestion:
    query: str
    relevant_article_id: str


_ARTICLES = [
    Article("vpn-connectivity", "Troubleshoot VPN connectivity", "Check VPN credentials, network access, and the tunnel status. Restart the client and capture its error code."),
    Article("phishing-report", "Report a suspicious phishing message", "Do not click suspicious links or enter passwords on unknown pages. Report the message to security and preserve it."),
    Article("account-unlock", "Unlock a locked account", "Verify identity, check account lockout status, then follow the approved account recovery process."),
    Article("outlook-startup", "Fix Outlook startup crashes", "Check Outlook add-ins, recent updates, and application logs. Compare with Outlook on the web."),
    Article("printer-queue", "Clear a stuck printer queue", "Confirm printer connectivity, cancel stuck jobs, and restart the print spooler if authorized."),
    Article("mfa-enrollment", "Enroll a device in MFA", "Register an authenticator or security key in the account security settings and verify the sign-in challenge."),
    Article("lost-device", "Report a lost or stolen device", "Contact security immediately, report the asset identifier, and request remote account and device protection."),
    Article("software-install", "Install approved software", "Find the approved package in the company software portal and request a license if required."),
]

_QUESTIONS = [
    HeldOutQuestion("My remote tunnel will not come up; what should I check?", "vpn-connectivity"),
    HeldOutQuestion("I typed credentials into a page from a suspicious email. What now?", "phishing-report"),
    HeldOutQuestion("How do I recover access after too many sign-in attempts?", "account-unlock"),
    HeldOutQuestion("The mail client closes on launch after an update.", "outlook-startup"),
    HeldOutQuestion("Documents are waiting forever and never leave the printer.", "printer-queue"),
    HeldOutQuestion("Where do I register a new authenticator for login verification?", "mfa-enrollment"),
    HeldOutQuestion("My company laptop is missing during a trip.", "lost-device"),
    HeldOutQuestion("Can I get the authorized package from the internal catalog?", "software-install"),
]

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {
    "a", "an", "and", "are", "after", "at", "do", "for", "from", "how", "i",
    "in", "is", "it", "my", "of", "on", "or", "the", "to", "what", "where",
    "will", "with", "you",
}


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in _TOKEN_PATTERN.findall(text.lower())
        if token not in _STOP_WORDS
    }


def _retrieve(query: str, limit: int = 3) -> list[str]:
    query_tokens = _tokens(query)
    ranked = []
    for article in _ARTICLES:
        article_tokens = _tokens(f"{article.title} {article.content}")
        score = len(query_tokens & article_tokens) / max(1, len(query_tokens))
        ranked.append((score, article.id))
    ranked.sort(key=lambda result: (-result[0], result[1]))
    return [article_id for score, article_id in ranked[:limit] if score > 0]


def retrieval_hit_rate() -> dict[str, float | int]:
    hits = sum(
        question.relevant_article_id in _retrieve(question.query)
        for question in _QUESTIONS
    )
    return {
        "hit_rate_at_3": round(hits / len(_QUESTIONS), 4),
        "hits": hits,
        "question_count": len(_QUESTIONS),
    }
