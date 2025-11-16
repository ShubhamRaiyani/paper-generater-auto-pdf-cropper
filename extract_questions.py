import sys
from pipeline.pdf_loader import load_pdf
from pipeline.index_builder import build_index
from interactive.report import print_index_report
from interactive.cli import interactive_crop

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_questions.py input.pdf")
        return

    pdf_path = sys.argv[1]
    print("Converting PDF to images...")
    pages = load_pdf(pdf_path, output_folder="temp_pages")

    print("Building index (detecting Q labels and question blocks)...")
    questions_index = build_index(pages, out_crops_folder="extracted_questions")

    print("\nIndex built.\n")
    print_index_report(questions_index)

    # enter interactive crop CLI
    interactive_crop(questions_index)

if __name__ == "__main__":
    main()
