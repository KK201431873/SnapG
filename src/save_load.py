from PySide6.QtWidgets import (
    QApplication
)

from styles.style_manager import get_style_sheet

from models import AppState

from pathlib import Path
import json

def load_state(app: QApplication, verbose: bool = False) -> AppState:
    """
    Retrieve the app state, otherwise default if invalid.
    Returns:
        save_state (AppState): The given `AppState` object.
    """
    json_path = Path(__file__).parent / "__appdata__" / "app_state.json"

    # check exists
    if not json_path.exists():
        return _write_state(json_path, AppState.default())
    
    # try reading file
    try:
        with open(json_path, 'r') as f:
            app_state = AppState.from_dict(json.load(f))

            # style sheet
            style_sheet = get_style_sheet(app_state.style.theme)
            app.setStyleSheet(style_sheet)

            if verbose:
                print(f"loaded theme [{app_state.style.theme}]: {style_sheet}")

            return app_state
    except Exception as e:
        return _write_state(json_path, AppState.default())


def _write_state(filepath: Path, app_state: AppState) -> AppState:
    """
    Attempt to write the default app state to the given file.
    Returns:
        save_state (AppState): The given `AppState` object.
    """
    save_state = app_state.model_dump()
    print(save_state)
    with open(filepath, 'w') as f:
        json.dump(save_state, f, indent=4)
    return app_state

