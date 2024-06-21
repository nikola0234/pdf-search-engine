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
        
        choice = input("Enter your choice: ")
        if choice == '1':
            query = input("Enter search query: ")
            page = 1
            results_per_page = 10
            
            while True:

                results = engine.search(query, page, results_per_page)

                if not results or len(results) < 3:  
                    alternative = engine.suggest_correction(query)
                    print(f"Did you mean: {alternative}?")
                    break

                print('\n' + '-' * 80)    
                print("PAGE NUMBER: ", page)
                for result_num, page_num, context in results:
                    print("-" * 80)
                    print(f"Result {result_num}: Page {page_num}")
                    print(f"Context: {context}")
                    print("-" * 80)
                
                next_page = input("Enter 'n' to see next page, 'p' for previous page, 'q' to quit: ")

                if next_page.lower() == 'n':
                    page += 1
                
                elif next_page.lower() == 'p' and page > 1:
                    page -= 1

                elif next_page.lower() == 'q':
                    break

        elif choice == '2':
            break

if __name__ == "__main__":
    main()
