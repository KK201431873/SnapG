import cv2
import numpy as np
import numpy.typing as npt
import math
from PIL import Image, ImageFont, ImageDraw
from pathlib import Path

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
        nm_per_pixel: float,
        thresh_val: int, 
        radius_val: int, 
        dilate: int, 
        erode: int, 
        min_size: int, 
        max_size: int, 
        convex_thresh: float, 
        circ_thresh: float,
        stop_flag
    ):
    h, w = input_image.shape
    linear_correction_ratio = 1.0 / resolution_divisor
    area_correction_ratio = linear_correction_ratio ** 2
    dilate = round(dilate * linear_correction_ratio)
    erode = round(erode * linear_correction_ratio)
    min_size = int(min_size * area_correction_ratio)
    max_size = int(max_size * area_correction_ratio)
    
    print()
    print("thresholding")
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
        return eroded, []
    
    print("getting contours")
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

        # Check if scale label interferes with the contour
        M = cv2.moments(c)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            x_limit = 290/1365*eroded.shape[0]
            y_limit = eroded.shape[1]-165/1365*eroded.shape[1]
            if cx<=x_limit and cy>= y_limit:
                continue

        filtered_contours.append(c)
    
    # Create output color image for visualization
    out_img = cv2.cvtColor(input_image, cv2.COLOR_GRAY2BGR)
    
    # Create binary mask of all contours
    all_contours_mask = np.zeros_like(eroded)
    cv2.drawContours(all_contours_mask, filtered_contours, -1, 255, thickness=cv2.FILLED)

    # return all_contours_mask, []
    
    print("drawing contours")
    data = [] # (ID, gratio, circularity, inner_diameter, outer_diameter, myelin_thickness)
    for i, contour in enumerate(filtered_contours):
        print(f"drawing contour {i}, stop_processing={stop_flag()}")
        if stop_flag():
            return out_img, data
        # Create mask of this contour
        contour_mask = np.zeros_like(eroded)
        cv2.drawContours(contour_mask, [contour], -1, 255, thickness=cv2.FILLED)

        # Compute center of mass of the contour
        moments = cv2.moments(contour)
        if moments["m00"] == 0:
            continue
        cx = int(moments["m10"] / moments["m00"])
        cy = int(moments["m01"] / moments["m00"])

        # Define bounding box around center of mass to crop candidate area
        search_radius = int(cv2.arcLength(contour, True) / (2*math.pi) + input_image.shape[0]/8)
        x_min = max(cx - search_radius, 0)
        x_max = min(cx + search_radius + 1, eroded.shape[1])
        y_min = max(cy - search_radius, 0)
        y_max = min(cy + search_radius + 1, eroded.shape[0])

        # Crop exclusion mask and eroded image
        cropped_eroded = eroded[y_min:y_max, x_min:x_max]
        cropped_contour_mask = contour_mask[y_min:y_max, x_min:x_max]

        # Build exclusion mask inside this cropped area
        exclusion_raw = ((cropped_contour_mask == 0) & (cropped_eroded == 255)).astype(np.uint8)
        exclusion_mask = cv2.Canny(exclusion_raw,0,0)
        distance = cv2.distanceTransform(255 - cropped_contour_mask, distanceType=cv2.DIST_L2, maskSize=5)[exclusion_mask > 0]

        # print(max([max(row) for row in distance]))
        # return cv2.bitwise_and((distance/max([max(row) for row in distance])*255).astype(np.uint8), exclusion_mask)
        
        # Flatten the array and filter out zeros
        nonzero_vals = distance[distance > 0]

        # Safety check: fewer than n nonzero values
        n = 2*len(contour)
        if len(nonzero_vals) < n:
            smallest = np.sort(nonzero_vals)
        else:
            # Get the n smallest nonzero values (unsorted)
            smallest = np.partition(nonzero_vals, n - 1)[:n]

        # Get thickness via percentile
        thickness = np.percentile(np.array(smallest), 30) # type: ignore

        ### generate visualization ###
        # Use distance transform
        distance = cv2.distanceTransform(255 - cropped_contour_mask, distanceType=cv2.DIST_L2, maskSize=5)

        # Draw outer and inner contours
        offset_mask = (distance <= thickness).astype(np.uint8) * 255
        offset_mask = offset_mask.astype(np.uint8)
        outer_contour, _ = cv2.findContours(offset_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        distance_inner = cv2.distanceTransform(offset_mask, cv2.DIST_L2, maskSize=5)
        offset_mask_eroded = (distance_inner > thickness).astype(np.uint8) * 255
        inner_contour, _ = cv2.findContours(offset_mask_eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        draw_scale = int(8*input_image.shape[0]/4096)

        # Calculate g-ratio
        contour_perimeter = cv2.arcLength(inner_contour[0], True)
        radius = contour_perimeter / (2*math.pi)
        g_ratio = radius / (radius + thickness)

        # Calculate circularity
        circularity = 4 * math.pi * cv2.contourArea(inner_contour[0]) / (contour_perimeter ** 2) if contour_perimeter != 0 else 0

        inner_diameter = (2*radius)*nm_per_pixel/resolution_divisor
        outer_diameter = inner_diameter + 2*thickness*nm_per_pixel*resolution_divisor
        
        # Draw contour and label thickness on output image
        cv2.drawContours(out_img, inner_contour + np.array([[[x_min, y_min]]]), -1, (0, 255, 0), draw_scale)
        cv2.drawContours(out_img, outer_contour + np.array([[[x_min, y_min]]]), -1, (0, 255, 0), draw_scale)
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"]-6*draw_scale)
            line_spacing = 14*draw_scale
            out_pil = Image.fromarray(cv2.cvtColor(out_img, cv2.COLOR_BGR2RGB))
            font_path = Path("assets/JetBrainsMono-Bold.ttf")
            font = ImageFont.truetype(font_path, max(15,int(15*draw_scale)))
            draw = ImageDraw.Draw(out_pil)

            # magic correction factors (i don't know if it works for images other than 4096px)
            if input_image.shape[0] < 512:
                x_correction_factor = 5*max(1, draw_scale)
                y_correction = 10*max(1,line_spacing)
            else:
                x_correction_factor = 5*draw_scale
                y_correction = 1/2*line_spacing
            def draw_white_id_text(dx,dy):
                draw.text((int(cx-x_correction_factor*len(f"#{i+1}"))+dx, cy-y_correction+dy), f"#{i+1}", font=font, fill=(255, 255, 255))
            for dx,dy in [(-2,-2),(2,-2),(2,2),(-2,2)]:
                draw_white_id_text(dx,dy)
            draw.text((int(cx-x_correction_factor*len(f"#{i+1}")), cy-y_correction), f"#{i+1}", font=font, fill=(0, 0, 0))
            inner_dia_text = f"ø{int(round(inner_diameter))}nm" if round(inner_diameter)<1000 else f"ø{inner_diameter/1000:.2f}μm"
            def draw_white_inner_dia_text(dx,dy):
                draw.text((int(cx-x_correction_factor*len(inner_dia_text)+dx), cy+y_correction+dy), inner_dia_text, font=font, fill=(255, 255, 255))
            for dx,dy in [(-2,-2),(2,-2),(2,2),(-2,2)]:
                draw_white_inner_dia_text(dx,dy)
            draw.text((int(cx-x_correction_factor*len(inner_dia_text)), cy+y_correction), inner_dia_text, font=font, fill=(0, 0, 255))

            out_img = cv2.cvtColor(np.array(out_pil), cv2.COLOR_RGB2BGR)
            
        data.append((i+1, float(g_ratio), float(circularity), float(inner_diameter), float(outer_diameter), float(thickness)))
        # print(f"myelin thickness {thickness} | axon radius {radius} | g_ratio {g_ratio}")
    
    return out_img, data