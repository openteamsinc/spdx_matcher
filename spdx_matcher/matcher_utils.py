from typing import Optional, Any
from .base_matcher import TransformResult


def to_dict(tr: Optional[TransformResult]) -> Any:
    if isinstance(tr, str):
        return tr

    if tr is None:
        return None

    return tr.to_dict()


def is_empty(p: Optional[TransformResult]) -> bool:
    if p is None:
        return True

    if isinstance(p, str):
        text = p.strip()
        if not text:
            return True
        # if text is a string of three or more '-','=' or '*'
        if len(text) >= 3 and all(c in "-=*" for c in text):
            return True

        return False

    return p.is_empty()
