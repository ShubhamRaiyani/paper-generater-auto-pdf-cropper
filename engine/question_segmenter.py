# engine/question_segmenter.py
import re
import cv2
import numpy as np
from pytesseract import image_to_string
import os

# ---------- Config (tune these) ----------
TOP_MARGIN = 10          # px to expand above a detected question start
BOTTOM_MARGIN = 15       # px to expand above the next start (so we don't cut bottom lines)
SAVE_DEBUG_CROPS = False # If True, saves per-region debug crops into DEBUG_OUT
DEBUG_OUT = "debug_question_crops"
# -----------------------------------------

# Anchored pattern: start-of-line, optional Q or Question, optional opening '(',
# then 1-3 digits followed by ., ) or :
QUESTION_START_PATTERN = re.compile(r'(?i)^\s*(?:Q(?:uestion)?\.?\s*)?\(?\s*\d{1,3}\s*[\.\)\:]', re.IGNORECASE)
PAREN_NUM_PATTERN = re.compile(r'^\(\s*(\d{1,2})\s*\)$')

def is_question_start(text):
    if not text:
        return False
    s = text.strip()
    prefix = s[:80]
    m = QUESTION_START_PATTERN.match(prefix)
    if not m:
        return False
    token = m.group().strip()
    if token.lower().startswith('q'):
        return True
    pm = PAREN_NUM_PATTERN.match(token)
    if pm:
        num = int(pm.group(1))
        if num >= 10:
            return True
        if re.search(r'\(\s*\d{1,2}\s*\)', s[m.end():]) or len(re.findall(r'\(\s*\d{1,2}\s*\)', s)) > 1:
            return False
        return False
    return True

def segment_questions(image_path, layout):
    """
    Compute full-width question regions on the page based only on Y positions.

    Args:
        image_path: path to the page image
        layout: iterable of blocks (expects .type and .coordinates -> (x1,y1,x2,y2))
                We use layout only to find candidate text blocks and their Y positions.
    Returns:
        List of dict blocks: {text, x1, y1, x2, y2}
        - x1 will be 0 and x2 will be page width (full width cropping)
    """
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Unable to read image: {image_path}")

    h, w = image.shape[:2]

    # Build candidates from layout: we only need vertical positions and the text for detecting starts.
    text_blocks = [b for b in layout if getattr(b, "type", "text").lower() == "text"]
    candidates = []
    for b in text_blocks:
        # normalize coordinates to ints
        x1, y1, x2, y2 = map(int, b.coordinates)
        # crop the block area for OCR text
        # guard against invalid coords
        y1c = max(0, min(h-1, y1))
        y2c = max(0, min(h, y2))
        x1c = max(0, min(w-1, x1))
        x2c = max(0, min(w, x2))
        if y2c - y1c <= 0 or x2c - x1c <= 0:
            continue
        crop = image[y1c:y2c, x1c:x2c]
        try:
            text = image_to_string(crop, lang='eng', config='--psm 6')
        except Exception:
            text = image_to_string(crop)
        candidates.append({
            "text": text.strip(),
            "y1": y1c,
            "y2": y2c,
            "x1": x1c,
            "x2": x2c
        })

    # Find blocks that are question starts. Use the top-most y of the block as the start anchor.
    starts = []
    for c in candidates:
        if is_question_start(c["text"]):
            starts.append({"y": c["y1"], "text": c["text"]})

    # If we detected no starts using layout blocks, fallback to whole-page OCR line scan
    if not starts:
        # Try line-level OCR on the full image to detect question headers
        try:
            data = pytesseract.image_to_data(image, output_type='dict', config='--psm 3', lang='eng')
            n = len(data['level'])
            for i in range(n):
                txt = (data['text'][i] or "").strip()
                if not txt:
                    continue
                if is_question_start(txt):
                    y_top = int(data['top'][i])
                    starts.append({"y": y_top, "text": txt})
        except Exception:
            # fallback: no starts found -> return full page as single block
            return [{
                "text": image_to_string(image, lang='eng', config='--psm 3').strip(),
                "x1": 0, "y1": 0, "x2": w, "y2": h
            }]

    # Normalize and sort starts by Y (top to bottom). Remove duplicates very close together.
    starts = sorted(starts, key=lambda s: s['y'])
    filtered = []
    last_y = -9999
    MIN_VERTICAL_SEPARATION = 8  # px; merge detections within this distance
    for s in starts:
        if s['y'] - last_y > MIN_VERTICAL_SEPARATION:
            filtered.append(s)
            last_y = s['y']
    starts = filtered

    # Compute full-width regions using only Y coordinates
    regions = []
    for i, s in enumerate(starts):
        start_y = max(0, s['y'] - TOP_MARGIN)
        if i + 1 < len(starts):
            next_y = starts[i+1]['y']
            end_y = max(start_y + 20, next_y - BOTTOM_MARGIN)  # ensure minimal height
        else:
            end_y = h
        end_y = min(h, end_y)

        # Make sure region height sensible
        if end_y <= start_y + 5:
            end_y = min(h, start_y + 30)

        region = {
            "text": s.get("text", "").strip(),
            "x1": 0,
            "y1": int(start_y),
            "x2": int(w),
            "y2": int(end_y)
        }
        regions.append(region)

    # Optionally save debug crops to disk so you can inspect them visually
    if SAVE_DEBUG_CROPS:
        os.makedirs(DEBUG_OUT, exist_ok=True)
        for idx, r in enumerate(regions, start=1):
            crop_img = image[r['y1']:r['y2'], r['x1']:r['x2']]
            debug_path = os.path.join(DEBUG_OUT, f"q_{idx}_y{r['y1']}_{r['y2']}.png")
            cv2.imwrite(debug_path, crop_img)

    # If somehow no regions detected, fallback to a single whole-page region
    if not regions:
        whole_text = image_to_string(image, lang='eng', config='--psm 3')
        regions = [{
            "text": whole_text.strip(),
            "x1": 0, "y1": 0, "x2": w, "y2": h
        }]

    return regions
