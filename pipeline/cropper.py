import os
import cv2

def crop_question_from_index(questions_index, page_num, qnum, output_folder="cropped_questions"):
    os.makedirs(output_folder, exist_ok=True)

    if page_num not in questions_index:
        raise KeyError(f"Page {page_num} not indexed")

    page_list = questions_index[page_num]
    entry = next((e for e in page_list if e["qnum"] == qnum), None)
    if entry is None:
        raise KeyError(f"Q{qnum} not found on page {page_num}")

    img = cv2.imread(entry["image_path"])
    if img is None:
        raise FileNotFoundError(entry["image_path"])
    h, w = img.shape[:2]
    b = entry["block"]
    # crop using block y1,y2 and full width
    crop = img[b["y1"]:b["y2"], b["x1"]:b["x2"]]
    out_path = os.path.join(output_folder, f"page{page_num}_Q{qnum}.png")
    cv2.imwrite(out_path, crop)
    return out_path
