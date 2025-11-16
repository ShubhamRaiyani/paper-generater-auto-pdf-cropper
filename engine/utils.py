import cv2
import os

def save_question_crops(image_path, blocks, output_folder):
    image = cv2.imread(image_path)
    base = os.path.basename(image_path).split(".")[0]

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    saved_files = []

    for i, b in enumerate(blocks):
        crop = image[b["y1"]:b["y2"], b["x1"]:b["x2"]]
        out_path = f"{output_folder}/{base}_q{i+1}.png"
        cv2.imwrite(out_path, crop)
        saved_files.append(out_path)

    return saved_files
