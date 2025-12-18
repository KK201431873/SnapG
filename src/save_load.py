from PySide6.QtWidgets import (
    QApplication
)


from models import AppState

from pathlib import Path
import json

app_state_path = Path(__file__).parent / "__appdata__" / "app_state.snpg"

def load_state(path: Path = app_state_path) -> tuple[AppState, bool]:
    """
    Retrieve the app state, otherwise default if invalid.
    Returns:
        save_state (AppState): The given `AppState` object.
        valid (bool): Whether the given file was valid or not.
    """

    # check exists
    if not path.exists():
        return write_state(AppState.default()), False
    
    # try reading file
    try:
        with open(path, 'r') as f:
            return AppState.from_dict(json.load(f)), True
    except Exception as e:
        return write_state(AppState.default()), False


def write_state(app_state: AppState, path: Path = app_state_path) -> AppState:
    """
    Attempt to write the given app state to the given file.
    Returns:
        save_state (AppState): The given `AppState` object.
    """
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    save_state = app_state.model_dump()
    with open(path, 'w') as f:
        json.dump(save_state, f, indent=4)
    return app_state

