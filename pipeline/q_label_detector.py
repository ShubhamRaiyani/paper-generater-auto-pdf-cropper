import re
import cv2
import pytesseract

QUESTION_TEXT_REGEX = re.compile(r"Q\s*(\d{1,4})\s*\.", re.IGNORECASE)

def detect_q_labels(image_path):
    """
    Return list of label dicts: [{'qnum': int, 'text': 'Q1.', 'x1':..,'y1':..,'x2':..,'y2':..'}, ...]
    Uses pytesseract image_to_data.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(image_path)

    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    results = []
    n = len(data["text"])
    for i in range(n):
        txt = (data["text"][i] or "").strip()
        if not txt:
            continue
        m = QUESTION_TEXT_REGEX.fullmatch(txt)
        if m:
            qnum = int(m.group(1))
            x = int(data["left"][i])
            y = int(data["top"][i])
            w = int(data["width"][i])
            h = int(data["height"][i])
            results.append({
                "text": txt,
                "qnum": qnum,
                "x1": x,
                "y1": y,
                "x2": x + w,
                "y2": y + h
            })
    # sort top-to-bottom by y1
    results.sort(key=lambda r: r["y1"])
    return results
