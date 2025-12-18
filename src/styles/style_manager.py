from pathlib import Path

_theme: str | None = None
_style_sheet: str | None = None # I don't know what type this is

def get_style_sheet(theme: str) -> str:
    """Returns style sheet as plaintext from the given qss theme file."""
    global _style_sheet, _theme
    if _style_sheet is None or _theme != theme:
        path = Path(__file__).parent / f"{theme}.qss"
        _theme = theme
        _style_sheet = path.read_text(encoding="utf-8")
    return _style_sheet

__all__ = ["get_style_sheet"]