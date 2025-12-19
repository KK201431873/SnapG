# SnapG

PySide6 application for partially automating myelinated axon segmentation in microscopy images.

---

## Installation

1. **Download** or clone this repository. To download this repository, scroll to the top of this GitHub page, click the green `<> Code` button, and then press `Download ZIP`. Then, extract the ZIP file.

2. **Install Python 3** if not already installed.

3. **Install dependencies**: Open a terminal in the `SnapG/` folder and run

    ```
    pip install -r requirements.txt
    ```

    If that doesn't work, try running

    ```
    py -m pip install -r requirements.txt
    ```

4. **Try opening the app**: For Mac users, open the `SnapG/` folder in Finder and double click the `SnapG.command` file. For Windows and Linux users, open a terminal in the `SnapG/` folder and run

    ```
    python src/main.py
    ```

    If that doesn't work, try either of the following commands

    ```
    python3 src/main.py
    py src/main.py
    ```

---

## How to Use SnapG

Before we start...

1. Open SnapG using one of the methods listed above. This window should appear:
  
    ![SnapG application window](images/snapg_window.png)

2. You're all set to start segmenting!


### Adjusting the View
Hover over the `View` menu in the top left. The following options should appear:

![View menu options](images/view_menu.png)

- **Panels**: You can show and hide the three panels using this menu.

- **Color Theme**: Only the "Light" theme is currently available. More may be added!

- **Reset View**: Click this option at any time to reset the widths and heights of the panels.


### Opening Images

In order to segment images, you'll need to import them into SnapG first!

1. Hover over the `File` menu in the top left, and click on `Open… >` then `Image file(s)`.
  
    ![Open image files](images/open_image_files.png)

2. A file dialog will open. Select your images and confirm!
  
    ![Open images dialog](images/open_images_dialog.png)

3. Your images should now be opened in the window.
  
    ![Loaded images](images/loaded_images.png)


### Controlling the Image

It's important to know how to navigate the image view to start segmenting images.

1. To **pan** the image, press and drag **Right Mouse Button** in the image panel.
  
    ![Panning the image view](images/pan_image_view.gif)

2. To **zoom** in and out, use the **Scroll Wheel** within the image panel.
  
    ![Zooming the image view](images/zoom_image_view.gif)


### Tuning the Segmentation Parameters

SnapG's segmentation algorithm is only semi-automated. However, SnapG's user interface aims to simplify the parameter tuning process, and gives the user greater control over the quality of its outputs!

1. I suggest you close the `Batch Processing` panel for this part and widen the `Segmentation Settings` panel for enhanced visibility.

2. In the `Segmentation Settings` panel, there are adjustable *Image Control* parameters and *OpenCV Parameters*. To learn what each parameter controls, hover your mouse over each of them to show the tooltip.
  
    ![Settings toolip](images/settings_tooltip.png)

    If the tooltip does not show up, you can find a list of each parameter's description [at the bottom of this README](#segmentation-parameter-descriptions).

3. Enter in your `Distance per pixel` value.
  
    ![Set distance per pixel](images/set_dist_per_px.png)

4. The only way to understand what each parameter does is to play around with them! First, *uncheck* the `Show Original` box and *check* the `Show Threshold` box.
  
    ![Untuned threshold](images/untuned_threshold.png)

5. Adjust the `Image Resolution Divisor` slider and the `Threshold`, `Radius`, `Dilate`, and `Erode` sliders until the black-and-white image looks smooth and representative of the original image. I recommend setting `Image Resolution Divisor` as high as possible without losing too much detail, since it increases processing speed (especially because I am using a 4096x4096 image!).
  
    ![Tuning threshold and radius](images/tune_threshold_radius.gif)

6. Next, *uncheck* the `Show Threshold` box and if you want, check the `Show Text` box (showing text may cause the image to process slower). Adjust the `Min size`, `Max size`, `Convexity`, `Circularity`, and `Thickness Percentile` sliders until axons and myelin are reliably detected in your images.
  
    ![Tuning min size](images/tune_min_size.gif)

    In this gif, I set `Min size = 0.0010` and then repeatedly press `Ctrl+Tab` to look through each image and verify that there are minimal false negatives.

    *NOTE*: You may notice that the `Min size` parameter is very sensitive. This is expected behavior, which is why you may provide up to four decimal places of accuracy.

7. Verify that the distance measurements are roughly accurate by looking at the data in the `Output` panel. 
  
    ![Output panel data](images/output_panel_data.gif)

8. Don't overthink the parameters! Sometimes, only a little bit of adjustment is needed to get a decent segmentation result.


### Batch Processing

Now that you have the appropriate parameters for your image set, it's time to batch process the whole set.

1. Show the `Batch Processing` panel by using the `View` menu in the top left. Press the `Choose Images` button at the top of the panel. This window should appear: 
  
    ![Batch processing choose images window](images/batch_choose_images.png)

2. Click `Add Images` and select the images you tuned the segmentation parameters for.
  
    ![Batch processing file list](images/batch_file_list.png)

3. Click `Select All`, check the `Check Selected` box in the top left of the window, and press `OK`. If you only want to process a part of your image set, uncheck the files you want to exclude from the batch process.
  
    ![Batch processing confirm files](images/batch_confirm_files.gif)

4. Press the `Choose Destination Path` button and select where you'd like SnapG to save segmentation files. SnapG will create a folder within your chosen folder to store the files.

5. Select whether you'd like to use multiprocessing. Multiprocessing lets the code process images in parallel using each of your computer's logical processors, which is especially useful for processing large images and/or a large number of images. It is recommended to select the maximum number of workers (another word for logical processor).
  
    ![Batch processing "processing options" section](images/batch_proc_options.png)

6. When you're ready, hit Start!
  
    ![Batch processing start processing](images/batch_start_proc.gif)

7. Check the folder where you saved your segmentation files. You should see a `.seg` file for each image that was processed.
  
    ![Batch processing segmentation files](images/batch_seg_files.png)


### Reviewing Segmentation Files

SnapG will produce false positive detections more often than not, so it's important to manually filter them out. But don't worry, SnapG's user interface simplifies the review process as well!

1. Close both the `Batch Processing` and `Segmentation Settings` panels. Hover over the `File` menu in the top left and click `Close multiple files`. 
  
    ![Close multiple files](images/close_mult_files.png)

2. Select all of the images, check the `Check Selected` box in the top left, and press `OK`. You don't need to have them open anymore.
  
    ![Close multiple files pressing OK](images/close_press_ok.gif)


3. Open the `File` menu in the top left, click on `Open… >` then `Segmentation file(s)`. Choose and open all of your `.seg` files.
  
    ![Loaded segmentation files](images/loaded_seg_files.png)

4. **Click a contour** to deselect it (turn it red) and click it again to re-select it (turn it back green). *Deselecting a contour does not delete it: the contour is just flagged to be ignored when generating segmentation data.* 
  
    ![Review deselect contours](images/review_deselect_contours.gif)
  
    Press **Shift** to hide deselected contours, and press **Space** to hide all contours. These controls make it easier to determine if a contour is a false positive.
  
    ![Review show/hide contours](images/review_show_hide.gif)

5. **Repeat** for each of your `.seg` files! Your changes save every time you click a contour, so you don't have to worry about losing your work.


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

## Segmentation Parameter Descriptions

As mentioned in the [Tuning the Segmentation Parameters](#tuning-the-segmentation-parameters) section, here is a list of each parameter's description to give you a better idea of how the segmentation algorithm works.

### Image Controls

- **Distance Per Pixel**: Conversion from image pixel distance to real distance. Scales with Image Resolution Divider. This parameter is used when generating CSV data from segmented images.

- **Image Resolution Divisor**: How much to downscale the image by. For example, a value of 4 would shrink a 4096x4096 image to 1024x1024 before feeding it into the segmentation algorithm.

- **Show Original**: Whether to show the original image file. Useful for visually validating contours and thresholds.

- **Show Threshold**: Whether to show the thresholded binary (black and white) image. Useful for tuning OpenCV parameters.

- **Show Text**: Whether to show axon numbers and g-ratios on the image. Useful for checking data in the Output panel.


---

## Development

TODO

Building:
Delete `__pycache__` directories:
```
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
```

Rebuild command (Run from `SnapG/`):
```
pyinstaller main.spec
```

---
