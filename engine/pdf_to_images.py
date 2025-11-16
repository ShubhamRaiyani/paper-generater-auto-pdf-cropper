# engine/pdf_to_images.py
from pdf2image import convert_from_path
import os

def pdf_to_images(pdf_path, output_folder, poppler_path=r"C:\poppler\poppler-25.11.0\Library\bin"):
    if not os.path.isabs(pdf_path):
        pdf_path = os.path.abspath(pdf_path)

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if not os.path.isdir(poppler_path):
        raise FileNotFoundError(f"Poppler path not found: {poppler_path}")

    pages = convert_from_path(pdf_path, 300, poppler_path=poppler_path)
    image_paths = []

    os.makedirs(output_folder, exist_ok=True)

    base = os.path.splitext(os.path.basename(pdf_path))[0]
    for i, page in enumerate(pages):
        img_path = os.path.join(output_folder, f"{base}_page_{i+1}.png")
        page.save(img_path, "PNG")
        image_paths.append(img_path)

    return image_paths
