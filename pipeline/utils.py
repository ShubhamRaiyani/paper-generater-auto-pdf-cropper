import cv2
import os

def save_crop(image_path, block, output_folder, prefix=None):
    """
    Save a block crop and return path.
    block: dict with x1,y1,x2,y2
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(image_path)
    os.makedirs(output_folder, exist_ok=True)
    crop = img[block["y1"]:block["y2"], block["x1"]:block["x2"]]
    if prefix:
        fname = f"{prefix}.png"
    else:
        base = os.path.splitext(os.path.basename(image_path))[0]
        fname = f"{base}_{block['y1']}_{block['y2']}.png"
    out = os.path.join(output_folder, fname)
    cv2.imwrite(out, crop)
    return out
