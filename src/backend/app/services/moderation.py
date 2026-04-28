"""
Content moderation and safety service
Phase 0: Safety baseline checks
"""

class ModerationService:
    """Service for content moderation and safety checks"""
    
    # Phase 0 Safety Baseline: Simple rule-based checks
    # Future: Replace with OpenAI Moderation API or Claude content policy
    
    SENSITIVE_PATTERNS = [
        # Violence/threats
        ("kill", 0.9),
        ("hurt", 0.8),
        ("bomb", 0.95),
        ("gun violence", 0.95),
        
        # Self-harm
        ("suicide", 0.95),
        ("self-harm", 0.95),
        
        # Illegal activities
        ("illegal drug", 0.9),
        ("hack", 0.7),
        ("steal", 0.8),
        
        # Adult content
        ("explicit sex", 0.9),
        
        # Discrimination
        ("hate", 0.8),
        ("racist", 0.95),
        ("sexist", 0.95),
    ]
    
    @staticmethod
    def check_content_safety(content: str) -> tuple[bool, list, float]:
        """
        Check if content passes safety baseline
        
        Phase 0 implementation: Rule-based pattern matching
        Future: Integrate Claude content policy or OpenAI Moderation
        
        Args:
            content: Text to check
        
        Returns:
            (passed: bool, flags: list, risk_score: float)
            - passed: True if content is safe
            - flags: List of flagged patterns
            - risk_score: 0.0-1.0 confidence that content is unsafe
        """
        content_lower = content.lower()
        flags = []
        max_risk = 0.0
        
        # Check against sensitive patterns
        for pattern, risk in ModerationService.SENSITIVE_PATTERNS:
            if pattern in content_lower:
                flags.append({
                    "pattern": pattern,
                    "risk": risk,
                })
                max_risk = max(max_risk, risk)
        
        # Threshold: if any flag > 0.7, content fails
        passed = max_risk < 0.7
        
        return passed, flags, max_risk
    
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
