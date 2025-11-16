def print_index_report(questions_index):
    total = 0
    for page, items in questions_index.items():
        print(f"Page {page}: {len(items)} questions ->", [e["qnum"] for e in items])
        total += len(items)
    print("Total questions indexed:", total)
