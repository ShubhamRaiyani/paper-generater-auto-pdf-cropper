# extract_questions.py
"""
Robust runner for the Page Understanding Engine (Phase 1).
Usage:
    python extract_questions.py [path/to/input.pdf]

If no argument is provided, it defaults to the PDF path set in DEFAULT_PDF.
Make sure to update TESSERACT_EXE and POPPLER_DIR below if they differ on your machine.
"""

import os
import sys
import traceback
import pytesseract

# ---------- CONFIG ----------
# Default PDF (used if no CLI arg)
DEFAULT_PDF = r"D:\New folder (2)\Parth\input.pdf"

# Poppler binary folder (contains pdfinfo, pdftoppm)
POPPLER_DIR = r"C:\poppler\poppler-25.11.0\Library\bin"

# Tesseract executable (use the full path to tesseract.exe to avoid PATH issues)
TESSERACT_EXE = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Output / temp folders (absolute recommended)
TEMP_DIR = r"D:\New folder (2)\Parth\temp_pages"
OUT_DIR = r"D:\New folder (2)\Parth\extracted_questions"
# ----------------------------

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def validate_executable(path, name):
    if not path:
        raise FileNotFoundError(f"{name} path is empty.")
    if not os.path.exists(path):
        raise FileNotFoundError(f"{name} not found at: {path}")

def main():
    # Accept PDF from CLI or fallback to DEFAULT_PDF
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF
    pdf_path = os.path.abspath(pdf_path)

    print("Runner starting.")
    print("PDF:", pdf_path)
    print("Poppler:", POPPLER_DIR)
    print("Tesseract (exe):", TESSERACT_EXE)
    print("Temp dir:", TEMP_DIR)
    print("Output dir:", OUT_DIR)
    print("-" * 60)

    # Basic checks
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found: {pdf_path}")
        sys.exit(1)

    if not os.path.isdir(POPPLER_DIR):
        print(f"ERROR: Poppler folder not found: {POPPLER_DIR}")
        print("Make sure Poppler is installed and POPPLER_DIR points to Library\\bin")
        sys.exit(1)

    # Set tesseract location for pytesseract to avoid PATH reliance
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE
    try:
        # quick check for tesseract availability
        validate_executable(TESSERACT_EXE, "Tesseract executable")
    except Exception as e:
        print("WARNING: Tesseract not found at configured path.")
        print("You can either add Tesseract to PATH or set TESSERACT_EXE to the correct path.")
        print("Exception:", e)
        sys.exit(1)

    # create folders
    ensure_dir(TEMP_DIR)
    ensure_dir(OUT_DIR)

    # lazy import engine modules now (so runner can fail with a clear message)
    try:
        from engine.pdf_to_images import pdf_to_images
        from engine.layout_detector import detect_layout
        from engine.question_segmenter import segment_questions
        from engine.utils import save_question_crops
    except Exception as e:
        print("ERROR: failed to import engine modules. Did you place the files under engine/?")
        traceback.print_exc()
        sys.exit(1)

    # Convert PDF -> images
    try:
        pages = pdf_to_images(pdf_path, TEMP_DIR, poppler_path=POPPLER_DIR)
    except Exception as e:
        print("ERROR: pdf_to_images failed.")
        traceback.print_exc()
        sys.exit(1)

    print(f"Converted PDF into {len(pages)} page images.")
    print("-" * 60)

    # Process each page individually so one error doesn't stop the whole run
    all_saved = []
    for idx, page_img in enumerate(pages, start=1):
        try:
            print(f"[{idx}/{len(pages)}] Processing page: {page_img}")
            layout = detect_layout(page_img)
            blocks = segment_questions(page_img, layout)
            saved = save_question_crops(page_img, blocks, OUT_DIR)
            print(f"    -> Saved {len(saved)} crops.")
            all_saved.extend(saved)
        except Exception as e:
            print(f"ERROR processing page {page_img}: {e}")
            traceback.print_exc()
            # continue to next page

    print("-" * 60)
    print(f"Done. Total crops saved: {len(all_saved)}")
    print("Output folder:", OUT_DIR)
    print("If crops are empty or wrong, inspect images in:", TEMP_DIR)
    print("Runner finished.")

if __name__ == "__main__":
    main()
