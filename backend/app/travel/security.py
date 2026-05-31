import re


INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous\s+)?instructions",
    r"you\s+are\s+now",
    r"system\s*prompt",
    r"forget\s+(everything|all)",
    r"act\s+as",
    r"jailbreak",
    r"<\s*script",
]


def sanitize_user_input(text: str) -> tuple[str, bool]:
    lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower):
            return text, True
    return text[:500], False


def mask_pii(text: str) -> str:
    text = re.sub(r"\b\d{12}\b", "[ИИН]", text)
    text = re.sub(
        r"(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}",
        "[ТЕЛЕФОН]",
        text,
    )
    return text
