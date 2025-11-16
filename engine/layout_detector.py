# import cv2
# import layoutparser as lp

# def detect_layout(image_path):
#     image = cv2.imread(image_path)
#     model = lp.Detectron2LayoutModel(
#         config_path="lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config",
#         label_map={0:"text", 1:"title", 2:"list", 3:"table", 4:"figure"}
#     )
#     layout = model.detect(image)
#     return layout
# engine/layout_detector.py
"""
Layout detection with fallback:
- Prefer Detectron2LayoutModel (if layoutparser+detectron2 installed)
- Fallback to OpenCV + pytesseract text bounding-box detection (works on Windows without heavy deps)
Returns a list of objects with attributes:
    - type: str (e.g. "text")
    - coordinates: [x1, y1, x2, y2]
This keeps the rest of your code (which expects layoutparser blocks) compatible.
"""

import cv2
import numpy as np
import os

# small helper class to mimic layoutparser block shape
class SimpleBlock:
    def __init__(self, _type, coords):
        self.type = _type
        # coords in layoutparser are typically (x1, y1, x2, y2)
        self.coordinates = coords

# First try: Detectron2 model via layoutparser (if available)
try:
    import layoutparser as lp
    # this attribute exists only when the extra detectron2 backend is present
    Detectron2LayoutModel = getattr(lp, "Detectron2LayoutModel", None)

    if Detectron2LayoutModel is not None:
        def detect_layout(image_path):
            image = cv2.imread(image_path)
            # initialize model once (cache on the function object)
            if not hasattr(detect_layout, "model"):
                detect_layout.model = lp.Detectron2LayoutModel(
                    config_path="lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config",
                    label_map={0: "text", 1: "title", 2: "list", 3: "table", 4: "figure"}
                )
            layout = detect_layout.model.detect(image)
            return layout
    else:
        raise ImportError("Detectron2LayoutModel not available in layoutparser")
except Exception:
    # Fallback implementation using OpenCV + pytesseract
    # This works well for text-heavy educational papers and is dependency-light.
    try:
        from pytesseract import image_to_data
    except Exception as e:
        raise ImportError(
            "Both Detectron2 layout model and pytesseract-based fallback are unavailable. "
            "Install pytesseract (`pip install pytesseract`) and ensure Tesseract is on PATH."
        ) from e

    def _merge_boxes(boxes, overlapThresh=0.2):
        # boxes: list of [x1,y1,x2,y2]
        if len(boxes) == 0:
            return []
        boxes = np.array(boxes).astype(int)
        x1 = boxes[:,0]
        y1 = boxes[:,1]
        x2 = boxes[:,2]
        y2 = boxes[:,3]

        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
        idxs = np.argsort(y1)  # sort by top y

        pick = []
        while len(idxs) > 0:
            last = idxs[0]
            pick.append(last)
            remove_idxs = [0]
            for pos in range(1, len(idxs)):
                i = last
                j = idxs[pos]

                xx1 = max(x1[i], x1[j])
                yy1 = max(y1[i], y1[j])
                xx2 = min(x2[i], x2[j])
                yy2 = min(y2[i], y2[j])

                w = max(0, xx2 - xx1 + 1)
                h = max(0, yy2 - yy1 + 1)
                inter = w * h
                overlap = inter / float(areas[j])

                # merge if overlapping vertically (same text line/paragraph)
                if overlap > overlapThresh or (abs(y1[i]-y1[j]) < 10):
                    remove_idxs.append(pos)

            idxs = np.delete(idxs, remove_idxs)
        merged = []
        for p in pick:
            merged.append([int(x1[p]), int(y1[p]), int(x2[p]), int(y2[p])])
        return merged

    def detect_layout(image_path):
        """
        Returns a list of SimpleBlock objects with .type and .coordinates
        """
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"Image not found or unreadable: {image_path}")

        # convert to RGB for pytesseract
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Use pytesseract to get word-level boxes and group them into blocks
        # `image_to_data` returns a TSV; each row has left, top, width, height for each detected word/line
        data = image_to_data(rgb, output_type='dict')

        n_boxes = len(data['level'])
        boxes = []
        for i in range(n_boxes):
            # filter out weak/confidence < 30
            conf = -1
            try:
                conf = int(data['conf'][i])
            except Exception:
                try:
                    conf = float(data['conf'][i])
                except Exception:
                    conf = -1
            if conf >= 20:
                (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                boxes.append([x, y, x + w, y + h])

        # Merge boxes that are on same line / close to each other to form text blocks
        merged = _merge_boxes(boxes, overlapThresh=0.15)

        # Convert to SimpleBlock objects
        blocks = [SimpleBlock("text", tuple(b)) for b in merged]

        # As a last resort, if no blocks detected, return a single full-page text block
        if len(blocks) == 0:
            h, w = img.shape[:2]
            blocks = [SimpleBlock("text", (0, 0, w, h))]

        return blocks
