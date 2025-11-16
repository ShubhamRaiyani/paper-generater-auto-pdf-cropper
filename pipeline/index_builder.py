import os
from .q_label_detector import detect_q_labels
from .block_segmenter import segment_blocks_from_labels
from .utils import save_crop

def build_index(pages, out_crops_folder="extracted_questions"):
    """
    pages: list of image paths
    Returns: questions_index: {page_num: [ {qnum,label,block,image_path,crop_path}, ... ] }
    """
    questions_index = {}
    os.makedirs(out_crops_folder, exist_ok=True)

    for page_number, page_path in enumerate(pages, start=1):
        # detect label boxes
        labels = detect_q_labels(page_path)
        # compute blocks (full-width)
        blocks = segment_blocks_from_labels(page_path, labels, full_width=True)

        page_entries = []
        for lbl, blk in zip(labels, blocks):
            # save individual block crop for quick preview
            out_path = save_crop(page_path, blk, out_crops_folder, prefix=f"page{page_number}_Q{lbl['qnum']}")
            page_entries.append({
                "qnum": lbl["qnum"],
                "label": lbl,
                "block": blk,
                "image_path": page_path,
                "crop_path": out_path
            })

        questions_index[page_number] = page_entries

    return questions_index
