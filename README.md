# SnapG

PySide6 application for partially automating myelinated axon segmentation in microscopy images.

---

## Installation

TODO

---

## How to Use

TODO

#### Adjusting the Sliders

- **Threshold**: Controls brightness threshold for identifying axon interiors.  
  _Higher = stricter, lower = more inclusive._

- **Radius**: Smooths edges and reduces noise.  
  _Higher = less detail._

- **Dilate**: Expands white pixel regions and fills gaps.

- **Erode**: Contracts white regions. Ideally, dilate and erode should be equal.

- **Minimum Size**: Minimum area (in thousands of pixels) for a contour to be recognized.

- **Maximum Size**: Maximum area (in thousands of pixels).

- **Convexity**: Filters out contours with low convexity.  
  _Convexity = Area / Convex Hull Area._

- **Circularity**: Filters out contours with low circularity.  
  _Circularity = 4π × Area / (Perimeter²)._

- **Toggle Contours**: Slide right to preview the algorithm’s detections.

#### Tuning Tips

- Start with all sliders at 0 except threshold. Tune threshold until the axon interiors are clearly isolated from the outside.
- Radius might not be useful in detailed images.
- Dilate and erode might not be useful in images that are crowded and detailed.
- You may not need to adjust min/max size often.
- It's better to have more false positives than false negatives. Therefore, it may be ideal to keep convexity and circularity at 0.

#### Save Your Settings

- Press **CTRL+S** to save current settings to a JSON file.
- Settings auto-save if the program is closed accidentally.

---

#### Buttons Instructions

Click these buttons in order:

- **Select Settings**: Choose the JSON settings file you saved.
- **Select Images**: Select the images you want to segment using these settings.
- **Process Images**: Choose an output folder. A "STOP" button will appear to the right if you need to cancel the operation.
  - This generates `.pkl` files containing contours and measurements for each image.
- **Review Output**: Select the `.pkl` files you want to review. Then, follow the instructions in the text box.
  - _Note: Disabling a contour in the reviewer doesn't delete it on exit; don't worry if you misclick._
- **Generate Data**: Select the `.pkl` files you want to generate a CSV file for. Then, choose an output folder to save your data to.

---

## Development

TODO

Rebuild command (Run from `SnapG/`):
```
pyinstaller main.spec
```

---
