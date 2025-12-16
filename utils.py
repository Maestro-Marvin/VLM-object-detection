import json
from PIL import Image, ImageDraw, ImageFont
from PIL import ImageColor
import re

additional_colors = [colorname for (colorname, colorcode) in ImageColor.colormap.items()]

def safe_json_load(text: str):
    """Attempt to load JSON, with fallbacks for malformed or wrapped content."""
    # Try to extract first ```json ... ``` block
    match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        text = match.group(1).strip()

    # Remove trailing commas, fix single quotes, etc.
    try:
        # Replace single quotes with double quotes (common in LLM outputs)
        text = re.sub(r"'([^']*)'", r'"\1"', text)
        # Remove trailing commas
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*\]', ']', text)
        return json.loads(text)
    except Exception as e:
        print(f"JSON parse failed: {e}")
        return None

def decode_json_points(text: str):
    """Parse coordinate points from text format, tolerant of thinking/reasoning"""
    data = safe_json_load(text)
    if not data:
        return [], []

    points = []
    labels = []
    
    # Handle both list and dict formats
    if isinstance(data, dict):
        data = [data]
    
    for item in data:
        if "point_2d" in item:
            try:
                x, y = item["point_2d"]
                points.append([float(x), float(y)])
                
                label = item.get("label", f"point_{len(points)}")
                labels.append(str(label))
            except (TypeError, ValueError):
                continue  # Skip malformed point
    
    return points, labels

def decode_json_bboxes(text: str):
    """Parse bounding box coordinates from text format, tolerant of thinking/reasoning"""
    data = safe_json_load(text)
    if not data:
        return [], []

    bboxes = []
    labels = []
    
    if isinstance(data, dict):
        data = [data]
    
    for item in data:
        if "bbox_2d" in item:
            try:
                coords = item["bbox_2d"]
                if len(coords) != 4:
                    continue
                x_min, y_min, x_max, y_max = map(float, coords)
                bboxes.append([x_min, y_min, x_max, y_max])
                
                label = item.get("label", f"bbox_{len(bboxes)}")
                labels.append(str(label))
            except (TypeError, ValueError):
                continue  # Skip malformed bbox
    
    return bboxes, labels

# --- Plotting functions remain mostly unchanged ---

def plot_points(img_path, text):
    img = Image.open(img_path)
    width, height = img.size
    draw = ImageDraw.Draw(img)
    colors = [
        'red', 'green', 'blue', 'yellow', 'orange', 'pink', 'purple', 'brown', 'gray',
        'beige', 'turquoise', 'cyan', 'magenta', 'lime', 'navy', 'maroon', 'teal',
        'olive', 'coral', 'lavender', 'violet', 'gold', 'silver',
    ] + additional_colors

    points, descriptions = decode_json_points(text)
    print("Parsed points: ", points)
    print("Parsed descriptions: ", descriptions)
    if not points:
        display(img)
        return

    for i, point in enumerate(points):
        color = colors[i % len(colors)]
        abs_x1 = point[0] * width
        abs_y1 = point[1] * height
        radius = 2
        draw.ellipse([(abs_x1 - radius, abs_y1 - radius), (abs_x1 + radius, abs_y1 + radius)], fill=color)
        draw.text((abs_x1 - 20, abs_y1 + 6), descriptions[i], fill=color)
    display(img)

def plot_bboxes(img_path, text):
    img = Image.open(img_path)
    width, height = img.size
    draw = ImageDraw.Draw(img)
    colors = [
        'red', 'green', 'blue', 'yellow', 'orange', 'pink', 'purple', 'brown', 'gray',
        'beige', 'turquoise', 'cyan', 'magenta', 'lime', 'navy', 'maroon', 'teal',
        'olive', 'coral', 'lavender', 'violet', 'gold', 'silver',
    ] + additional_colors

    bboxes, descriptions = decode_json_bboxes(text)
    print("Parsed bboxes: ", bboxes)
    print("Parsed descriptions: ", descriptions)
    
    if not bboxes:
        display(img)
        return

    for i, bbox in enumerate(bboxes):
        color = colors[i % len(colors)]
        x_min, y_min, x_max, y_max = bbox
        
        # Convert to absolute pixel coordinates
        abs_x_min = x_min * width
        abs_y_min = y_min * height
        abs_x_max = x_max * width
        abs_y_max = y_max * height
        
        # Draw bounding box
        draw.rectangle(
            [(abs_x_min, abs_y_min), (abs_x_max, abs_y_max)], 
            outline=color, 
            width=2
        )
        
        # Draw label
        label_pos_x = abs_x_min
        label_pos_y = abs_y_min - 15 if abs_y_min > 15 else abs_y_min + 5
        draw.text((label_pos_x, label_pos_y), descriptions[i], fill=color)
    
    display(img)