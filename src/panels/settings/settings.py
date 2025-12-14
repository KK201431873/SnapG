from pydantic import BaseModel

class Settings(BaseModel):
    """Data class to store segmentation settings."""

    scale: float
    """Distance per pixel."""
    
    scale_units: str
    """Unit of distance per pixel (either µm or nm)."""

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
