import cv2

TOP_MARGIN = 6    # expand start a bit above label
BOTTOM_MARGIN = 8 # shrink a bit before next label (avoids cutting last line)

def segment_blocks_from_labels(image_path, label_boxes, full_width=True):
    """
    Given an image and sorted label_boxes (list of dicts with y1, y2),
    compute full-question blocks: x1,x2,y1,y2 for each label.
    Returns list of blocks in same order as label_boxes.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(image_path)
    h, w = img.shape[:2]

    blocks = []
    n = len(label_boxes)
    for i, lb in enumerate(label_boxes):
        start_y = max(0, lb["y1"] - TOP_MARGIN)
        if i + 1 < n:
            # next label's top is cutoff
            next_y = label_boxes[i+1]["y1"]
            end_y = max(start_y + 20, next_y - BOTTOM_MARGIN)
        else:
            end_y = h
        x1 = 0 if full_width else lb["x1"]
        x2 = w if full_width else lb["x2"]
        blocks.append({
            "qnum": lb["qnum"],
            "x1": int(x1),
            "y1": int(start_y),
            "x2": int(x2),
            "y2": int(end_y)
        })
    return blocks
