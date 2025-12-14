from PySide6.QtWidgets import (
    QApplication
)


from models import AppState

from pathlib import Path
import json

app_state_path = Path(__file__).parent / "__appdata__" / "app_state.json"

def load_state() -> AppState:
    """
    Retrieve the app state, otherwise default if invalid.
    Returns:
        save_state (AppState): The given `AppState` object.
    """

    # check exists
    if not app_state_path.exists():
        return write_state(AppState.default())
    
    # try reading file
    try:
        with open(app_state_path, 'r') as f:
            return AppState.from_dict(json.load(f))
    except Exception as e:
        return write_state(AppState.default())


def write_state(app_state: AppState) -> AppState:
    """
    Attempt to write the default app state to the given file.
    Returns:
        save_state (AppState): The given `AppState` object.
    """
    if not app_state_path.exists():
        app_state_path.parent.mkdir(parents=True, exist_ok=True)
    save_state = app_state.model_dump()
    with open(app_state_path, 'w') as f:
        json.dump(save_state, f, indent=4)
    return app_state

