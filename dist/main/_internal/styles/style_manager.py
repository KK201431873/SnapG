from models import FileMan

_theme: str | None = None
_style_sheet: str | None = None

def get_style_sheet(theme: str) -> str:
    """Returns style sheet as plaintext from the given qss theme file."""
    global _style_sheet, _theme
    if _style_sheet is None or _theme != theme:
        path = FileMan.resource_path(f"styles/{theme}.qss")
        _theme = theme
        _style_sheet = path.read_text(encoding="utf-8")
    return _style_sheet

__all__ = ["get_style_sheet"]