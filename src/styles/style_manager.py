from pathlib import Path

_style_sheet: str | None = None # I don't know what type this is

def get_style_sheet(theme: str) -> str:
    """Returns style sheet as plaintext from the given qss theme file."""
    global _style_sheet
    if _style_sheet is None:
        path = Path(__file__).parent / f"{theme}.qss"
        _style_sheet = path.read_text(encoding="utf-8")
    return _style_sheet

__all__ = ["get_style_sheet"]