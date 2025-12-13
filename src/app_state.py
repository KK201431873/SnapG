from PySide6.QtWidgets import (
    QApplication
)

from styles.style_manager import get_style_sheet

from pathlib import Path
import json
import sys


def load_save_state(app: QApplication, verbose: bool = False):
    """Load the app's last save state."""
    try:
        save_state = _load_json_file()

        # style sheet
        style = save_state['style']
        style_sheet = get_style_sheet(style['theme'])
        app.setStyleSheet(style_sheet)
        if verbose:
            print(f"loaded theme [{style['theme']}]: {style_sheet}")
    except Exception as e:
        print(f"Exception while loading app save state: {e}")
        sys.exit(1)


def _load_json_file() -> dict:
    """Retrieve the app save state as a dict, otherwise default if invalid."""
    json_path = Path(__file__).parent / "__appdata__" / "save_state.json"

    # check exists
    if not json_path.exists():
        return _write_default_save_state(json_path)
    
    # try reading file
    try:
        with open(json_path, 'r') as f:
            save_state: dict = json.load(f)
            return save_state
    except Exception as e:
        return _write_default_save_state(json_path)


def _write_default_save_state(filepath: Path) -> dict:
    """
    Attempt to write the default save state to the given file.
    Returns:
        save_state (dict): Dictionary representing app save state.
    """
    save_state = {
        "style": {
            "theme": "light"
        }
    }
    with open(filepath, 'w') as f:
        json.dump(save_state, f, indent=4)
    return save_state