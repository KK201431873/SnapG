from models import SegmentationData, ContourData

from PIL import Image, ImageFont, ImageDraw
from pathlib import Path
import numpy.typing as npt
import numpy as np
import cv2

def get_csv_lines(seg_data_list: list[SegmentationData], 
                  font_path: Path, 
                  formatted_datetime: str
    ) -> tuple[
        list[tuple[str, npt.NDArray]],
        list[str]
    ]:
    """Generate a CSV representation of the data from `SegmentationData` objects."""
    out_imgs: list[tuple[str, npt.NDArray]] = []
    data_lists: list[tuple[str, list[ContourData], str]] = []
    for seg_data in seg_data_list:
        # unpack data
        img_filename = seg_data.img_filename
        display_img = seg_data.image.copy()
        contour_data = seg_data.contour_data
        selected_states = seg_data.selected_states
        
        # reindex selected contours
        included_ids = [ID for ID, keep in enumerate(selected_states) if keep] # ID is zero-indexed
        reindexed_contour_data = [c for ID, c in enumerate(contour_data) if ID in included_ids] # use enumerate() to get the IDs

        # draw contours
        for c in reindexed_contour_data:
            M = cv2.moments(c.inner_contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            color = (0, 255, 0)
            cv2.drawContours(display_img, [c.inner_contour], -1, color, 2)
            cv2.drawContours(display_img, [c.outer_contour], -1, color, 2)

        # draw text
        img_h = display_img.shape[0]
        img_w = display_img.shape[1]
        draw_scale = int(8 * max(img_h, img_w) / 4096)
        line_spacing = 14*draw_scale
        out_pil = Image.fromarray(cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB))
        font = ImageFont.truetype(font_path, max(15, int(15 * draw_scale)))
        draw = ImageDraw.Draw(out_pil)
        for i, c in enumerate(reindexed_contour_data):
            M = cv2.moments(c.inner_contour)
            if M["m00"] == 0:
                continue
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"] - 6*draw_scale)

            if max(img_h, img_w) < 512:
                x_corr = 5 * max(1, draw_scale)
                y_corr = 10 * max(1, line_spacing)
            else:
                x_corr = 5 * draw_scale
                y_corr = 0.5 * line_spacing

            ID = i + 1
            label = f"#{ID}"

            color = (255, 255, 255)
            def draw_shadow_text(dx,dy):
                draw.text((int(cx-x_corr*len(label))+dx, cy-y_corr+dy), label, font=font, fill=color)
            for dx,dy in [(-2,-2),(2,-2),(2,2),(-2,2)]:
                draw_shadow_text(dx,dy)
            color = (0, 0, 0)
            draw.text((int(cx-x_corr*len(label)), cy-y_corr), label, font=font, fill=color)
            
        display_img = cv2.cvtColor(np.array(out_pil), cv2.COLOR_RGB2BGR)
        
        name, extension = img_filename.split(".")
        if extension == "":
            extension = ".tif" # default .tif
        out_imgs.append((f"{name}_labeled_{formatted_datetime}.{extension}", display_img))
        data_lists.append((img_filename, reindexed_contour_data, seg_data.preferred_units))
    
    # get axon metrics
    g_ratios: list[float] = []
    for _, contour_data_list, preferred_units in data_lists:
        units_factor: float = 1.0
        if preferred_units == "nm": # convert to um
            units_factor = 1.0 / 1000.0
        g_ratios += [c.g_ratio * units_factor for c in contour_data_list]
    n_axons = len(g_ratios)
    g_ratio_mean = np.mean(g_ratios)
    g_ratio_stdev = np.std(g_ratios)
    g_ratio_se = g_ratio_stdev / np.sqrt(n_axons)
        
    # Create csv lines
    csv_lines: list[str] = []
    
    csv_lines.append(f"Metrics for all axons\n")
    csv_lines.append(f"Number of axons,{n_axons:.4f}\n")
    csv_lines.append(f"Mean G-ratio (um),{g_ratio_mean:.4f}\n")
    csv_lines.append(f"G-ratio Stdev (um),{g_ratio_stdev:.4f}\n")
    csv_lines.append(f"G-ratio SE (um),{g_ratio_se:.4f}\n")
    csv_lines.append(f"\n")

    csv_lines.append(f"Image,Axons found\n")
    for filename, data, _ in data_lists:
        csv_lines.append(f"{filename},{len(data)}\n")
    csv_lines.append(f"Total,{sum([len(data) for _,data,_ in data_lists])}\n")
    csv_lines.append("\n")

    for filename, data, preferred_units in data_lists:
        csv_lines.append(f"{filename}\n")
        csv_lines.append(f"Axon #,G-ratio,Circularity,Inner diameter ({preferred_units}),Outer diameter ({preferred_units}),Myelin Thickness ({preferred_units})\n")
        for axon_id, c in enumerate(data):
            gratio = c.g_ratio
            circularity = c.circularity
            inner_dia = c.inner_diameter # nm
            outer_dia = c.outer_diameter # nm
            thickness = c.thickness # nm
            if preferred_units == "um":
                inner_dia /= 1000.0
                outer_dia /= 1000.0
                thickness /= 1000.0
            csv_lines.append(f"{axon_id + 1},{gratio:.4f},{circularity:.4f},{inner_dia:.4f},{outer_dia:.4f},{thickness:.4f}\n")
        csv_lines.append("\n")

    return out_imgs, csv_lines