import re


def normalize_name(name: str) -> str:
    """
    Normalize a person's name for identity comparison.

    Example:
        GADEWAR SOHAN
        Sohan Gadewar

    Both become:
        gadewar sohan
    """

    name = str(name or "").strip().lower()

    name = re.sub(
        r"[^a-z0-9\s]",
        " ",
        name,
    )

    parts = name.split()

    parts = [
        part
        for part in parts
        if part
    ]

    return " ".join(
        sorted(parts)
    )