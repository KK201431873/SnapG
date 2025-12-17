from models import ContourData

import cv2
import numpy as np
import numpy.typing as npt
import math
from PIL import Image, ImageFont, ImageDraw
from pathlib import Path

import time

def clamp(x, lower, upper):
    """Clamps `x` between `lower` and `upper`."""
    return max(lower, min(upper, x))

def create_circular_kernel(radius):
    """Create a circular kernel mask"""
    size = 2 * radius + 1
    y, x = np.ogrid[-radius:radius+1, -radius:radius+1]
    mask = x*x + y*y <= radius*radius
    return mask.astype(np.float32)

def convexness(contour, hull):
    contour_area = cv2.contourArea(contour)
    hull_area = cv2.contourArea(hull)
    return contour_area/hull_area

def process_image(
        input_image: npt.NDArray, 
        resolution_divisor: float,
        show_thresholded: bool,
        show_text: bool,
        nm_per_pixel: float,
        thresh_val: int, 
        radius_val: int, 
        dilate: int, 
        erode: int, 
        min_size: int, 
        max_size: int, 
        convex_thresh: float, 
        circ_thresh: float,
        thickness_percentile: int,
        stop_flag,
        font_path: Path | None,
        verbose = False,
        timed = False
    ) -> tuple[npt.NDArray, list[ContourData] | None]:
    h, w = input_image.shape
    linear_correction_ratio = 1.0 / resolution_divisor
    area_correction_ratio = linear_correction_ratio ** 2
    dilate = round(dilate * linear_correction_ratio)
    erode = round(erode * linear_correction_ratio)
    min_size = int(min_size * area_correction_ratio)
    max_size = int(max_size * area_correction_ratio)
    
    if timed:
        very_start_time = time.perf_counter()
        if verbose:
            print()
            print("thresholding")
            start_time = very_start_time

    # Threshold image (binary)
    kernel = create_circular_kernel(radius_val)
    kernel_sum = np.sum(kernel)
    kernel /= kernel_sum
    img = cv2.filter2D(src=input_image, ddepth=-1, kernel=kernel)
    _, thresh = cv2.threshold(img, thresh_val, 255, cv2.THRESH_BINARY)

    # Remove small black features
    inverted = cv2.bitwise_not(thresh)
    contours, _ = cv2.findContours(inverted, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    for c in contours:
        if cv2.contourArea(c) < 1000 * area_correction_ratio:
            cv2.drawContours(thresh, [c], -1, 255, cv2.FILLED)
    
    # # Remove small long white features
    # contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    # for c in contours:
    #     if cv2.contourArea(c) < 10000 * area_correction_ratio:
    #         cv2.drawContours(thresh, [c], -1, 0, cv2.FILLED)

    # Dilate image
    dilate_size = max(1, int(dilate))
    dilate_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (dilate_size,dilate_size))
    dilated = cv2.morphologyEx(thresh, cv2.MORPH_DILATE, dilate_kernel)

    # Dilate image
    erode_size = max(1, int(erode))
    erode_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (erode_size,erode_size))
    eroded = cv2.morphologyEx(dilated, cv2.MORPH_ERODE, erode_kernel)

    if show_thresholded:
        return eroded, None # None means don't analyze data
    
    if timed:
        if verbose:
            now = time.perf_counter()
            print(f"thresh took {now-start_time}s") # type: ignore
            print("getting contours")
            start_time = now

    # Find contours
    contours, _ = cv2.findContours(eroded, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    
    # Filter contours by size and convexness
    filtered_contours = []
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    for c in contours:
        # Check if contour touches edge of image
        if np.any(c[:, 0, 0] <= 1) or np.any(c[:, 0, 0] >= (w-2)) or \
           np.any(c[:, 0, 1] <= 1) or np.any(c[:, 0, 1] >= (h-2)):
            continue
        
        # Check if inner edge is black
        bx, by, bw, bh = cv2.boundingRect(c)
        eroded_roi = eroded[by:by+bh, bx:bx+bw]
        mask_shape = (bh, bw)
        full_mask = np.zeros(mask_shape, dtype=np.uint8)
        shifted_c = c - [bx, by]
        cv2.drawContours(full_mask, [shifted_c], -1, color=255, thickness=cv2.FILLED)
        eroded_mask1 = cv2.erode(full_mask, kernel, iterations=1)
        eroded_mask2 = cv2.erode(eroded_mask1, kernel, iterations=1)
        inner_edge_mask = cv2.subtract(eroded_mask1, eroded_mask2) # 1 pixel thick inner edge
        inner_pixels = eroded_roi[inner_edge_mask == 255]
        if len(inner_pixels) == 0 or np.mean(inner_pixels) < 128: # type: ignore
            continue
        
        # Check size
        c_area = cv2.contourArea(c)
        if not (min_size <= c_area <= max_size):
            continue
        
        # Check convexness
        hull = cv2.convexHull(c, returnPoints=True)
        convex = convexness(c, hull)
        if convex < convex_thresh:
            continue
        
        # Check circularity
        circularity = 4 * math.pi * cv2.contourArea(c) / (cv2.arcLength(c, closed=True) ** 2) if cv2.arcLength(c, closed=True) != 0 else 0
        if circularity < circ_thresh:
            continue

        filtered_contours.append(c)
    
    # Create output color image for visualization
    if font_path is not None:
        out_img = cv2.cvtColor(input_image, cv2.COLOR_GRAY2BGR)
    else:
        out_img = np.zeros(0)
    
    # Create binary mask of all contours
    all_contours_mask = np.zeros_like(eroded)
    cv2.drawContours(all_contours_mask, filtered_contours, -1, 255, thickness=cv2.FILLED)

    # return all_contours_mask, []
    
    if timed:
        now = time.perf_counter()
        if verbose:
            print(f"contours took {now-start_time}s") # type: ignore
            print(f"drawing {len(filtered_contours)} contours")
        start_time = now

    data: list[ContourData] = []

    TWO_PI = 2 * math.pi
    img_h = input_image.shape[0]
    img_w = input_image.shape[1]
    draw_scale = int(8 * img_h / 4096)

    if font_path is not None:
        font = ImageFont.truetype(font_path, max(15, int(15 * draw_scale)))
    else:
        font = None

    # Text drawing helper
    def draw_text(text, x, y, color, font, shadow=True):
        # white rectangular shadow
        if shadow:
            bbox = draw.textbbox((x, y), text, font=font)
            pad = max(1, int(draw_scale))
            draw.rectangle(
                (
                    bbox[0] - pad,
                    bbox[1] - pad,
                    bbox[2] + pad,
                    bbox[3] + pad,
                ),
                fill=(255, 255, 255)
            )
        # black text
        draw.text((x, y), text, font=font, fill=color)

    # Draw contours/text
    give_up = False # len(filtered_contours) > 150
    for i, contour in enumerate(filtered_contours):
        if give_up:
            break

        if stop_flag():
            return out_img, data

        # Compute center of mass of the contour
        M = cv2.moments(contour)
        if M["m00"] == 0:
            continue

        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        # Create mask of this contour
        contour_mask = np.zeros_like(eroded)
        cv2.drawContours(contour_mask, [contour], -1, 255, cv2.FILLED)

        # Define bounding box around center of mass to crop candidate area
        search_radius = int(cv2.arcLength(contour, True) / TWO_PI + img_h / 8)
        x_min = max(cx - search_radius, 0)
        x_max = min(cx + search_radius + 1, eroded.shape[1])
        y_min = max(cy - search_radius, 0)
        y_max = min(cy + search_radius + 1, eroded.shape[0])

        cropped_mask = contour_mask[y_min:y_max, x_min:x_max]
        cropped_eroded = eroded[y_min:y_max, x_min:x_max]

        # Build exclusion mask inside this cropped area
        exclusion_raw = ((cropped_mask == 0) & (cropped_eroded == 255)).astype(np.uint8)
        exclusion_edges = cv2.Canny(exclusion_raw, 0, 0)

        # distance transform (computed once)
        dist = cv2.distanceTransform(255 - cropped_mask, cv2.DIST_L2, 5)
        distance_samples = dist[exclusion_edges > 0]

        # Thickness estimation
        nonzero_vals = distance_samples[distance_samples > 0]
        if nonzero_vals.size == 0:
            continue

        n = 2 * len(contour)
        if len(nonzero_vals) < n:
            smallest = nonzero_vals
        else:
            smallest = np.partition(nonzero_vals, n - 1)[:n]

        thickness_px = np.percentile(smallest, thickness_percentile) # type: ignore

        ### generate visualization ###
        offset = np.array([[[x_min, y_min]]])

        offset_mask = (dist <= thickness_px).astype(np.uint8) * 255
        outer_contour, _ = cv2.findContours(offset_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        outer_contour += offset

        dist_inner = cv2.distanceTransform(offset_mask, cv2.DIST_L2, 5)
        offset_mask_eroded = (dist_inner > thickness_px).astype(np.uint8) * 255
        inner_contour, _ = cv2.findContours(offset_mask_eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        inner_contour += offset

        # Calculate g-ratio & circularity
        inner_contour_perimeter = cv2.arcLength(inner_contour[0], True)
        inner_radius = inner_contour_perimeter / TWO_PI
        outer_radius = cv2.arcLength(outer_contour[0], True) / TWO_PI

        g_ratio = inner_radius / outer_radius
        circularity = (
            4 * math.pi * cv2.contourArea(inner_contour[0]) / (inner_contour_perimeter ** 2)
            if inner_contour_perimeter != 0 else 0
        )

        inner_diameter = (2 * inner_radius) * nm_per_pixel * resolution_divisor
        outer_diameter = (2 * outer_radius) * nm_per_pixel * resolution_divisor
        thickness = thickness_px * nm_per_pixel * resolution_divisor

        # Draw contours on output image
        if font is not None:
            cv2.drawContours(out_img, inner_contour, -1, (0, 255, 0), draw_scale)
            cv2.drawContours(out_img, outer_contour, -1, (0, 255, 0), draw_scale)

            # text
            cx_text = cx
            cy_text = int(cy - 6 * draw_scale)
            line_spacing = 14 * draw_scale

            out_pil = Image.fromarray(cv2.cvtColor(out_img, cv2.COLOR_BGR2RGB))

            if show_text:
                draw = ImageDraw.Draw(out_pil)

                if img_h < 512:
                    x_corr = 5 * max(1, draw_scale)
                    y_corr = 10 * max(1, line_spacing)
                else:
                    x_corr = 5 * draw_scale
                    y_corr = 0.5 * line_spacing

                label = f"#{i+1}"

                draw_text(
                    label,
                    int(cx_text - x_corr * len(label)),
                    int(cy_text - y_corr),
                    (0, 0, 0),
                    font
                )

                inner_text = (
                    f"G:{g_ratio:.2f}"
                )

                draw_text(
                    inner_text,
                    int(cx_text - x_corr * len(inner_text)),
                    int(cy_text + y_corr),
                    (255, 255, 0),
                    font,
                    shadow=False
                )

            out_img = cv2.cvtColor(np.array(out_pil), cv2.COLOR_RGB2BGR)

        # Store results
        data.append(ContourData(
            ID = i + 1,
            inner_contour=inner_contour[0],
            outer_contour=outer_contour[0],
            g_ratio=float(g_ratio),
            circularity=float(circularity),
            inner_diameter=float(inner_diameter),
            outer_diameter=float(outer_diameter),
            thickness=float(thickness)
        ))

        # give up if taking too long (>5s)
        if timed:
            now = time.perf_counter()
            if now - very_start_time > 5: # type: ignore
                give_up = True

    # Give up if too many contours
    if give_up and font_path is not None:
        out_pil = Image.fromarray(cv2.cvtColor(out_img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(out_pil)
        img_size = max(img_w, img_h)
        size = 7
        if img_size <= 128:
            size = 7 + clamp(int((12-7)*(img_size-82)/(128-82)), 0, 12-7)
        elif img_size <= 512:
            size = 12 + clamp(int((40-12)*(img_size-128)/(447-128)), 0, 40-12)
        elif img_size <= 1170:
            size = 40 + clamp(int((100-40)*(img_size-512)/(1170-512)), 0, 100-40)
        else: # size 4096
            size = 100 + clamp(int((350-100)*(img_size-1170)/(4096-1170)), 0, 350-100)
        # print(size)
        font = ImageFont.truetype(font_path, size)
        draw_text("Too Much Work!", 0, 3*size, (0,0,0), font, shadow=True)
        draw_text("(Try increasing", 0, 4.5*size, (0,0,0), font, shadow=True)
        draw_text("resolution divider", 0, 6*size, (0,0,0), font, shadow=True)
        draw_text("or minimum size)", 0, 7.5*size, (0,0,0), font, shadow=True)
        out_img = cv2.cvtColor(np.array(out_pil), cv2.COLOR_RGB2BGR)
        return out_img, data
    
    if timed:
        if verbose:
            now = time.perf_counter()
            print(f"drawing took {now-start_time}s") # type: ignore
    
    return out_img, data