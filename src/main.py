from pdfSearchEngine import PdfSearchEngine 
import os
import trie

def main():
    index_file = '../trie.pkl'
    pdf_path = '../Data Structures and Algorithms in Python.pdf'

    engine = PdfSearchEngine(pdf_path, index_file)
    
    if os.path.exists(index_file):
        engine.load_index()
        print("Index loaded from file.")
    else:
        engine.index_pdf()
        engine.save_index()
        print("Index built and saved to file.")

    engine.calculate_page_rank()

    trie = engine.get_trie()

    while True:
        print("1. Search")
        print("2. Exit")
        print("3. Write page")
        
        choice = input("Enter your choice: ")
        if choice == '1':
            query = input("Enter search query: ")
            results = engine.search(query)
            for result_num, page_num, context in results:
                print("-" * 80)
                print(f"Result {result_num}: Page {page_num}")
                print(f"Context: {context}")
                print("-" * 80)
        elif choice == '2':
            break

        elif choice == '3':
            trie.print_trie()

if __name__ == "__main__":
    main()
