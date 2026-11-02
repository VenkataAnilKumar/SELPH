"""
Content moderation and safety service
Phase 0: Safety baseline checks
"""

import re

# (regex, risk, category). Regexes use word boundaries so "skills" never matches "kill".
_SAFETY_RULES: list[tuple[str, float, str]] = [
    # Violence / threats
    (r"\bkill(?:s|ed|ing|er)?\b", 0.9, "violence"),
    (r"\bhurt(?:s|ing)?\b", 0.8, "violence"),
    (r"\bbomb(?:s|ing)?\b", 0.95, "violence"),
    (r"\bgun violence\b", 0.95, "violence"),
    # Self-harm
    (r"\bsuicid(?:e|al)\b", 0.95, "self_harm"),
    (r"\bself[- ]harm\b", 0.95, "self_harm"),
    # Illegal activity
    (r"\billegal drugs?\b", 0.9, "illegal"),
    (r"\bhack(?:s|ed|ing|er|ers)?\b(?!athon)", 0.7, "illegal"),
    (r"\bsteal(?:s|ing)?\b", 0.8, "illegal"),
    # Adult content
    (r"\bexplicit sex\b", 0.9, "adult"),
    # Discrimination
    (r"\bhate(?:d|s)?\b", 0.8, "discrimination"),
    (r"\bracist\b", 0.95, "discrimination"),
    (r"\bsexist\b", 0.95, "discrimination"),
    # Hard blocks: the twin must never give financial, legal or medical direction on its own.
    (r"\b(?:wire|transfer|send)\s+(?:the\s+)?(?:money|funds|payment)\b", 0.9, "hard_block_financial"),
    (r"\b(?:bank account|routing number|credit card number|iban|seed phrase|private key)\b", 0.9, "hard_block_financial"),
    (r"\bguarantee[sd]?\s+(?:you\s+)?(?:returns?|profits?)\b", 0.9, "hard_block_financial"),
    (r"\b(?:legal advice|you should sue|sign the contract|you are liable|statute of limitations)\b", 0.9, "hard_block_legal"),
    (r"\b\d+\s?(?:mg|mcg|ml)\b", 0.9, "hard_block_medical"),
    (r"\b(?:diagnos(?:e|is|ed)|prescri(?:be|ption)|dosage|medical advice)\b", 0.9, "hard_block_medical"),
]

# Untrusted inbound text trying to steer the twin.
_INJECTION_RULES: list[tuple[str, float]] = [
    (r"ignore (?:all |any |the )?(?:previous|prior|above|earlier) (?:instructions|prompts?|rules)", 0.9),
    (r"disregard (?:all |any |the )?(?:previous|prior|above|earlier|your) (?:instructions|prompts?|rules)", 0.9),
    (r"\b(?:reveal|show|print|repeat) (?:me )?(?:your|the) (?:system )?prompt\b", 0.9),
    (r"\byou are now\b.{0,40}\b(?:dan|jailbroken|unfiltered|developer mode)\b", 0.9),
    (r"\bnew instructions\s*:", 0.8),
    (r"\bact as (?:if you (?:are|were)|the)\b.{0,40}\b(?:owner|admin|system)\b", 0.8),
]

_COMPILED_SAFETY = [(re.compile(p, re.IGNORECASE), r, c) for p, r, c in _SAFETY_RULES]
_COMPILED_INJECTION = [(re.compile(p, re.IGNORECASE), r) for p, r in _INJECTION_RULES]

PASS_THRESHOLD = 0.7


class ModerationService:
    """Rule-based content moderation and safety checks (local, no external API)."""

    @staticmethod
    def check_content_safety(content: str) -> tuple[bool, list, float]:
        """
        Check generated content against safety and hard-block rules.

        Returns (passed, flags, risk_score). Each flag has `pattern`, `risk` and `category`.
        """
        flags = []
        max_risk = 0.0
        for rx, risk, category in _COMPILED_SAFETY:
            match = rx.search(content or "")
            if match:
                flags.append({"pattern": match.group(0).lower(), "risk": risk, "category": category})
                max_risk = max(max_risk, risk)
        return max_risk < PASS_THRESHOLD, flags, max_risk

    @staticmethod
    def check_prompt_injection(content: str) -> list:
        """Flag inbound messages that try to override the twin's instructions."""
        flags = []
        for rx, risk in _COMPILED_INJECTION:
            match = rx.search(content or "")
            if match:
                flags.append({"pattern": match.group(0).lower(), "risk": risk, "category": "prompt_injection"})
        return flags

    @staticmethod
    def check_sensitive_incoming(content: str) -> list:
        """
        Flag inbound messages that need the human, not a reply: self-harm, or requests
        for medical, legal or financial direction. A templated reply is wrong for these.
        """
        flags = []
        for rx, risk, category in _COMPILED_SAFETY:
            if category == "self_harm" or category.startswith("hard_block_"):
                match = rx.search(content or "")
                if match:
                    flags.append({
                        "pattern": match.group(0).lower(),
                        "risk": risk,
                        "category": "sensitive_incoming",
                        "topic": category,
                    })
        return flags

    @staticmethod
    def moderate_reply(incoming: str, draft: str) -> tuple[bool, list, float]:
        """Moderate a drafted reply plus the untrusted inbound message that triggered it."""
        passed, flags, risk = ModerationService.check_content_safety(draft)
        extra = (
            ModerationService.check_prompt_injection(incoming)
            + ModerationService.check_sensitive_incoming(incoming)
        )
        if extra:
            flags = flags + extra
            risk = max([risk] + [f["risk"] for f in extra])
            passed = risk < PASS_THRESHOLD
        return passed, flags, risk

    @staticmethod
    def get_confidence_label(score: float) -> str:
        """
        Map confidence score to label
        
        Args:
            score: 0.0-1.0 confidence score
        
        Returns:
            "High", "Medium", or "Low"
        """
        if score >= 0.75:
            return "High"
        elif score >= 0.50:
            return "Medium"
        else:
            return "Low"
    
    @staticmethod
    def calculate_confidence_score(
        user_interaction_count: int = 1,
        moderation_passed: bool = True,
        topic_match: float = 0.5,
    ) -> float:
        """
        Calculate confidence score for a draft
        
        Phase 0 baseline calculation:
        - More user interactions → higher confidence
        - Moderation pass required
        - Topic match contribution
        
        Args:
            user_interaction_count: How many times user interacted with topic
            moderation_passed: Whether content passed safety checks
            topic_match: 0.0-1.0 how well it matches known topics
        
        Returns:
            0.0-1.0 confidence score
        """
        if not moderation_passed:
            return 0.1  # Very low confidence if moderation failed
        
        # Base score from topic match
        base_score = topic_match
        
        # Boost from user interaction history
        interaction_boost = min(user_interaction_count * 0.05, 0.3)  # Max 0.3 boost
        
        # Final score
        confidence = min(base_score + interaction_boost, 1.0)
        
        return confidence
    
    @staticmethod
    def suggest_moderation_action(content: str, flags: list) -> str:
        """
        Suggest whether to allow, warn, or block content
        
        Phase 0: Simple rule-based
        Future: More nuanced based on flags and context
        
        Args:
            content: The content being reviewed
            flags: List of safety flags
        
        Returns:
            "allow", "warn", or "block"
        """
        if not flags:
            return "allow"
        
        # If any high-risk flag, block
        if any(f["risk"] > 0.85 for f in flags):
            return "block"
        
        # If multiple medium-risk flags, warn
        if len([f for f in flags if f["risk"] > 0.7]) >= 2:
            return "warn"
        
        # If single medium-risk flag, allow with warning
        if any(f["risk"] > 0.7 for f in flags):
            return "warn"
        
        return "allow"
