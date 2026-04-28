"""
Twin learning service — updates the twin profile based on user feedback signals.

Phase 3.4 implementation:
  approved → reinforce: add draft content to vocab pool, keep current avg_response_length
  edited   → adapt: adjust avg_response_length toward edited length, merge new words into vocab
  rejected → note: no positive reinforcement; nothing changes (learning from explicit reject
             would require a reason field; that is a Phase 4+ extension)
  skip     → no signal; ignored

All changes are small incremental nudges to avoid over-fitting to a single interaction.
"""

from sqlalchemy.orm import Session
from app.models import Twin


# Maximum words to keep in the vocab list to prevent unbounded growth
_MAX_VOCAB = 200

# Weight for exponential moving average when adjusting avg_response_length
# e.g. 0.1 means "10% of new sample, 90% of existing value"
_RESPONSE_LENGTH_ALPHA = 0.1


class TwinLearningService:
    """Adjusts the twin's stored profile after user feedback actions."""

    @staticmethod
    def learn_from_approval(db: Session, twin_id: str, draft_content: str) -> None:
        """
        Called when user approves a draft without edits.
        Reinforces current style by extracting vocabulary from the approved content.
        """
        twin = db.query(Twin).filter(Twin.id == twin_id).first()
        if not twin:
            return

        TwinLearningService._absorb_vocab(twin, draft_content)
        db.commit()

    @staticmethod
    def learn_from_edit(
        db: Session,
        twin_id: str,
        original_content: str,
        edited_content: str,
    ) -> None:
        """
        Called when user edits a draft before approving.
        Adapts avg_response_length toward the edited length and absorbs edited vocab.
        """
        twin = db.query(Twin).filter(Twin.id == twin_id).first()
        if not twin:
            return

        # Nudge avg_response_length toward the user's preferred length
        edited_length = len(edited_content.split())
        new_avg = int(
            round(
                (1 - _RESPONSE_LENGTH_ALPHA) * twin.avg_response_length
                + _RESPONSE_LENGTH_ALPHA * edited_length
            )
        )
        twin.avg_response_length = max(10, new_avg)  # never go below 10 words

        # Absorb vocabulary from the edited (preferred) version, not the original
        TwinLearningService._absorb_vocab(twin, edited_content)
        db.commit()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _absorb_vocab(twin: Twin, text: str) -> None:
        """
        Extract significant words from text and merge into twin.vocab.
        Keeps the list bounded to _MAX_VOCAB items (FIFO eviction of oldest entries).
        """
        # Simple tokenisation: lowercase words, strip punctuation, min length 4
        import re
        raw_words = re.findall(r"[a-zA-Z']{4,}", text.lower())

        # Common stop-words to ignore
        _STOP = {
            "that", "this", "with", "have", "will", "from", "they", "been",
            "your", "what", "when", "there", "their", "about", "which",
            "would", "could", "should", "just", "like", "some", "then",
            "than", "more", "also", "very", "into", "over", "after",
        }
        new_words = [w for w in raw_words if w not in _STOP]

        existing: list = list(twin.vocab) if twin.vocab else []
        existing_set = set(existing)

        for word in new_words:
            if word not in existing_set:
                existing.append(word)
                existing_set.add(word)

        # Trim to max vocab size (keep most recently added — tail of list)
        if len(existing) > _MAX_VOCAB:
            existing = existing[-_MAX_VOCAB:]

        twin.vocab = existing
