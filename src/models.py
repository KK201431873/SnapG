from pydantic import BaseModel

class Style(BaseModel):
    """Data class to store style options."""

    theme: str
    """Application color theme (only `light` supported so far)."""

    @staticmethod
    def from_dict(style_dict: dict) -> 'Style':
        """Load a `Style` object from the given dictionary."""
        return Style(
            theme=style_dict['theme']
        )
    
    @staticmethod
    def default() -> 'Style':
        """Return the default `Style` options."""
        return Style(
            theme="light"
        )


class Settings(BaseModel):
    """Data class to store segmentation settings."""

    scale: float
    """Distance per pixel."""
    
    scale_units: str
    """Unit of distance per pixel (either `µm` or `nm`)."""

    show_original: bool
    """Show the original image or not."""

    show_threshold: bool
    """Show the thresholded or annotated image (overridden by show_original)."""

    threshold: int
    """Grayscale to binary threshold."""

    radius: int
    """Smoothing kernel radius."""

    dilate: int
    """Dilate kernel radius."""

    erode: int
    """Erode kernel radius."""

    min_size: int
    """Minimum contour size (px)."""

    max_size: int
    """Maximum contour size (px)."""

    convexity: float
    """Convexity percentage threshold (between `0.0` and `1.0`)."""

    circularity: float
    """Circularity percentage threshold (between `0.0` and `1.0`)."""

    @staticmethod
    def from_dict(settings_dict: dict) -> 'Settings':
        """Load a `Settings` object from the given dictionary."""
        return Settings(
            scale=settings_dict['scale'],
            scale_units=settings_dict['scale_units'],
            show_original=settings_dict['show_original'],
            show_threshold=settings_dict['show_threshold'],
            threshold=settings_dict['threshold'],
            radius=settings_dict['radius'],
            dilate=settings_dict['dilate'],
            erode=settings_dict['erode'],
            min_size=settings_dict['min_size'],
            max_size=settings_dict['max_size'],
            convexity=settings_dict['convexity'],
            circularity=settings_dict['circularity']
        )
    
    @staticmethod
    def default() -> 'Settings':
        """Return the default `Settings` options."""
        return Settings(
            scale=0.0,
            scale_units="µm",
            show_original=True,
            show_threshold=False,
            threshold=0,
            radius=0,
            dilate=0,
            erode=0,
            min_size=0,
            max_size=0,
            convexity=0.0,
            circularity=0.0
        )


class AppState(BaseModel):
    """Wrapper data class containing all app options."""

    style: Style
    """Style options."""

    settings: Settings
    """Segmentation settings."""

    @staticmethod
    def from_dict(app_state_dict: dict) -> 'AppState':
        """Load an `AppState` object from the given dictionary."""
        return AppState(
            style=Style.from_dict(app_state_dict['style']),
            settings=Settings.from_dict(app_state_dict['settings'])
        )
    
    @staticmethod
    def default() -> 'AppState':
        """Return the default `AppState` options."""
        return AppState(
            style=Style.default(),
            settings=Settings.default()
        )
