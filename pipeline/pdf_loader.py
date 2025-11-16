from pdf2image import convert_from_path
import os
import platform

def load_pdf(pdf_path, output_folder="temp_pages", poppler_path=None, dpi=300):
    """
    Convert PDF to PNG pages and return list of image paths.
    """
    if poppler_path is None:
        if platform.system().lower() == "windows":
            poppler_path = r"C:\poppler\poppler-25.11.0\Library\bin"
        else:
            poppler_path = "/usr/bin"

    if not os.path.isabs(pdf_path):
        pdf_path = os.path.abspath(pdf_path)

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    os.makedirs(output_folder, exist_ok=True)

    pages = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
    image_paths = []
    base = os.path.splitext(os.path.basename(pdf_path))[0]

    for i, page in enumerate(pages):
        img_path = os.path.join(output_folder, f"{base}_page_{i+1}.png")
        page.save(img_path, "PNG")
        image_paths.append(img_path)

    return image_paths
