"""Room text cleaning utilities."""

from .text_utils import norm_text


def clean_room(room_text: str) -> str:
    """Normalize room text. Placeholder for future room-specific cleaning rules."""
    cleaned_text = norm_text(room_text)
    return cleaned_text

