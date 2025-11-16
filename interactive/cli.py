from pipeline.cropper import crop_question_from_index

def interactive_crop(questions_index):
    print("Interactive crop CLI. Enter 0 to exit.")
    while True:
        try:
            s = input("Enter page number (0 to exit): ").strip()
            if not s:
                continue
            page = int(s)
            if page == 0:
                break
            q = int(input("Enter question number to crop: ").strip())
            out = crop_question_from_index(questions_index, page, q)
            print("Saved crop:", out)
        except Exception as e:
            print("Error:", e)
