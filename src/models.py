"""Utility and data classes used throughout the app."""
from PySide6.QtCore import (
    QObject,
    Signal
)

from pydantic import BaseModel, ConfigDict
import numpy.typing as npt
import numpy as np


class View(BaseModel):
    """Data class to store view options."""

    theme: str
    """Application color theme (only `light` supported so far)."""

    process_panel_visible: bool
    """Visibility of `ProcessPanel`."""

    settings_panel_visible: bool
    """Visibility of `SettingsPanel`."""

    output_panel_visible: bool
    """Visibility of `OutputPanel`."""

    process_panel_width: int
    """Width of `ProcesPanel` (px)."""

    settings_panel_width: int
    """Width of `ProcesPanel` (px)."""

    output_panel_height: int
    """Height of `ProcesPanel` (px)."""

    @staticmethod
    def from_dict(view_dict: dict) -> 'View':
        """Load a `View` object from the given dictionary."""
        return View(
            theme=view_dict['theme'],

            process_panel_visible=view_dict['process_panel_visible'],
            settings_panel_visible=view_dict['settings_panel_visible'],
            output_panel_visible=view_dict['output_panel_visible'],

            process_panel_width=view_dict['process_panel_width'],
            settings_panel_width=view_dict['settings_panel_width'],
            output_panel_height=view_dict['output_panel_height']
        )
    
    @staticmethod
    def default() -> 'View':
        """Return the default `View` options."""
        return View(
            theme="light",

            process_panel_visible=True,
            settings_panel_visible=True,
            output_panel_visible=True,

            process_panel_width=300,
            settings_panel_width=300,
            output_panel_height=200
        )


class Settings(BaseModel):
    """Data class to store segmentation settings."""

    scale: float
    """Distance per pixel."""
    
    scale_units: str
    """Unit of distance per pixel (either `µm` or `nm`)."""

    resolution_divisor: float
    """Factor to shrink the resolution of the image by before processing."""

    show_original: bool
    """Show the original image or not."""

    show_threshold: bool
    """Show the thresholded or annotated image (overridden by show_original)."""

    show_text: bool
    """Show the annotated image's text (overridden by `show_original` and `show_threshold`)."""

    threshold: int
    """Grayscale to binary threshold (between `0` and `255`)."""

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

    thickness_percentile: int
    """Percentile used to extract myelin thickness data from a thickness distribution."""

    @staticmethod
    def from_dict(settings_dict: dict) -> 'Settings':
        """Load a `Settings` object from the given dictionary."""
        return Settings(
            scale=settings_dict['scale'],
            scale_units=settings_dict['scale_units'],
            resolution_divisor=settings_dict['resolution_divisor'],
            show_original=settings_dict['show_original'],
            show_threshold=settings_dict['show_threshold'],
            show_text=settings_dict['show_text'],
            threshold=settings_dict['threshold'],
            radius=settings_dict['radius'],
            dilate=settings_dict['dilate'],
            erode=settings_dict['erode'],
            min_size=settings_dict['min_size'],
            max_size=settings_dict['max_size'],
            convexity=settings_dict['convexity'],
            circularity=settings_dict['circularity'],
            thickness_percentile=settings_dict['thickness_percentile']
        )
    
    @staticmethod
    def default() -> 'Settings':
        """Return the default `Settings` options."""
        return Settings(
            scale=1.0,
            scale_units="nm",
            resolution_divisor=3.0,
            show_original=True,
            show_threshold=True,
            show_text=False,
            threshold=127,
            radius=0,
            dilate=0,
            erode=0,
            min_size=100,
            max_size=1_000_000,
            convexity=0.0,
            circularity=0.0,
            thickness_percentile=30
        )


class ImagePanelState(BaseModel):
    """Data class to store the state of `ImagePanel`. **NOTE:** Non-primitive objects were converted for serialization. They must be converted back."""

    image_files: list[str]
    """List of loaded image files. **NOTE:** `Path` objects were converted to `str`s for serialization. They must be converted back."""

    seg_files: list[str]
    """List of loaded segmentation files. **NOTE:** `Path` objects were converted to `str`s for serialization. They must be converted back."""

    current_file: str
    """Currently displayed file. **NOTE:** `Path` was converted to `str` for serialization. It must be converted back."""

    mode: int
    """Current image viewing mode. **NOTE:** `image_panel.Mode` was converted to `int` for serialization. It must be converted back."""

    #NOTE: Not including current_image and current_seg_data here because the types get too clunky. Use ImagePanel.update_image()

    view_center_point: tuple[int, int]
    """Center point of the image in `ImageView`."""

    view_image_width: int
    """Width (i.e. zoom amount) of the image in `ImageView`."""

    @staticmethod
    def from_dict(image_panel_state_dict: dict) -> 'ImagePanelState':
        """Load a `ImagePanelState` object from the given dictionary."""
        return ImagePanelState(
            image_files=image_panel_state_dict['image_files'],
            seg_files=image_panel_state_dict['seg_files'],
            current_file=image_panel_state_dict['current_file'],
            mode=image_panel_state_dict['mode'],
            view_center_point=image_panel_state_dict['view_center_point'],
            view_image_width=image_panel_state_dict['view_image_width']
        )
    
    @staticmethod
    def default() -> 'ImagePanelState':
        """Return the default `ImagePanelState` options."""
        return ImagePanelState(
            image_files=[],
            seg_files=[],
            current_file="",
            mode=0,
            view_center_point=(0,0),
            view_image_width=300
        )
    

class ProcessPanelState(BaseModel):
    """Data class to store the state of `ProcessPanel`. **NOTE:** `Path`s was converted to `str`s for serialization. They must be converted back."""
    
    chosen_images: list[tuple[str, bool]]
    """List map of `Path`s (converted to `str`s) to `bool`s representing whether they are flagged for batch processing."""

    destination_path: str
    """Destination path for image processing results."""

    use_multiprocessing: bool 
    """Whether to use multiprocessing for batch processing."""
    
    @staticmethod
    def from_dict(process_panel_state_dict: dict) -> 'ProcessPanelState':
        """Load a `ProcessPanelState` object from the given dictionary."""
        return ProcessPanelState(
            chosen_images=process_panel_state_dict['chosen_images'],
            destination_path=process_panel_state_dict['destination_path'],
            use_multiprocessing=process_panel_state_dict['use_multiprocessing']
        )
    
    @staticmethod
    def default() -> 'ProcessPanelState':
        """Return the default `ProcessPanelState` options."""
        return ProcessPanelState(
            chosen_images=[],
            destination_path="",
            use_multiprocessing=True
        )


class AppState(BaseModel):
    """Wrapper data class containing all app options."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    view: View
    """View options."""

    settings: Settings
    """Segmentation settings."""

    image_panel_state: ImagePanelState
    """`ImagePanel` state."""

    process_panel_state: ProcessPanelState
    """`ProcessPanel` state."""

    @staticmethod
    def from_dict(app_state_dict: dict) -> 'AppState':
        """Load an `AppState` object from the given dictionary."""
        return AppState(
            view=View.from_dict(app_state_dict['view']),
            settings=Settings.from_dict(app_state_dict['settings']),
            image_panel_state=ImagePanelState.from_dict(app_state_dict['image_panel_state']),
            process_panel_state=ProcessPanelState.from_dict(app_state_dict['process_panel_state'])
        )
    
    @staticmethod
    def default() -> 'AppState':
        """Return the default `AppState` options."""
        return AppState(
            view=View.default(),
            settings=Settings.default(),
            image_panel_state=ImagePanelState.default(),
            process_panel_state=ProcessPanelState.default()
        )


# == imgproc stuff ==
class ContourData(BaseModel):
    """Cotainer class for the data representing one axon contour in a segmented image."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    ID: int
    """Axon ID."""

    inner_contour: npt.NDArray[np.int32]
    """Myelin inner contour."""

    outer_contour: npt.NDArray[np.int32]
    """Myelin outer contour."""

    g_ratio: float
    """Myelin G-ratio."""

    circularity: float
    """Inner contour circularity."""

    thickness: float
    """Myelin thickness."""

    inner_diameter: float
    """Inner myelin diameter."""

    outer_diameter: float
    """Outer myelin diameter."""

class SegmentationData(BaseModel):
    """Container class for segmentation data (i.e. data stored in a .seg file)."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    img_filename: str
    """File name of the segmented image."""

    image: npt.NDArray
    """Image object."""

    resolution_divisor: float
    """How much the resolution of the image was shrunk by for processing."""

    contour_data: list[ContourData]
    """List of `ContourData` objects for each axon."""

    selected_states: list[bool]
    """List of toggle states for each axon."""


class FileMan():
    """Utility class for file management."""

    @staticmethod
    def image_extensions() -> set[str]:
        """Return a set of valid image extension strings."""
        return {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.seg'}

    @staticmethod
    def is_image(extension: str) -> bool:
        """
        Returns:
            bool: Whether the given file extension represents an image.
        """
        return extension in FileMan.image_extensions()


class Logger(QObject):
    """Connects to `OutputPanel`'s text display and can be used anywhere to print logs."""

    printTriggered = Signal(str, bool, bool, bool, str)
    """Append a string to the text display."""

    clearTriggered = Signal()
    """Clear the text display."""

    def print(self, 
              s: str, 
              bold: bool = False,
              italic: bool = False,
              underline: bool = False,
              color: str = "black"
        ):
        """
        Append a string to the text display.
        Params:
            s (str): String to display.
            bold (bool): Bold option.
            italic (bool): Italic option.
            underline (bool): Underline option.
            color (str): Standard HTML color.
        """
        self.printTriggered.emit(str(s), bold, italic, underline, color)
    
    def println(self, 
              s: str, 
              bold: bool = False,
              italic: bool = False,
              underline: bool = False,
              color: str = "black"
        ):
        """
        Append a string followed by a newline to the text display.
        Params:
            s (str): String to display.
            bold (bool): Bold option.
            italic (bool): Italic option.
            underline (bool): Underline option.
            color (str): Standard HTML color.
        """
        self.print(str(s) + "\n", bold, italic, underline, color)
    
    def clear(self):
        """Clear the text display."""
        self.clearTriggered.emit()

# Create singleton instance of Logger
logger = Logger()
