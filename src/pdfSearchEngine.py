import re
import os
import PyPDF2
from trie import Trie
from termcolor import colored
import pickle
from gaph import Graph

class PdfSearchEngine:
    def __init__(self, path, index_file):
        self.path = path
        self.index_file = index_file
        self.trie = Trie()
        self.graph = Graph()
        self.pages_text = []
        self.is_indexed = False

    def index_pdf(self):
        with open(self.path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            self.pages_text = [page.extract_text() for page in pdf.pages]
            for page_num, text in enumerate(self.pages_text):
                self.index_page(text, page_num)
                self.graph.add_node(page_num)
                self.find_references(text, page_num)
        self.is_indexed = True

    def index_page(self, text, page_num):
        words = re.findall(r'\b\w+\b', text)
        for word in words:
            self.trie.insert(word.lower(), page_num)

    def find_references(self, text, page_num):
        references = re.findall(r'page\s+(\d+)', text, re.IGNORECASE)
        for ref in references:
            ref_page = int(ref) - 1
            self.graph.add_node(ref_page)
            self.graph.add_edge(page_num, ref_page)

    def save_index(self):
        with open(self.index_file, 'wb') as f:
            data = {
                'trie': self.trie,
                'pages_text': self.pages_text,
                'graph': self.graph
            }
            pickle.dump(data, f)
    
    def load_index(self):
        with open(self.index_file, 'rb') as f:
            data = pickle.load(f)
            self.trie = data['trie']
            self.pages_text = data['pages_text']
            self.graph = data['graph']
        self.is_indexed = True
            
    def search(self, query):
        if not self.is_indexed:
            raise ValueError("Index not built or loaded")
        query_words = query.lower().split()
        results = {}

        for word in query_words:
            pages = self.trie.search(word)
            for page in pages:
                if page not in results:
                    results[page] = 0
                results[page] += 1

        sorted_results = sorted(results.items(), key=lambda item: item[1], reverse=True)
        search_results = []

        for i, (page_num, count) in enumerate(sorted_results):
            context = self.get_context(self.pages_text[page_num], query_words)
            search_results.append((i + 1, page_num + 1, context))

        return search_results

    def get_context(self, text, query_words, context_size=30):
        text_lower = text.lower()
        positions = [m.start() for word in query_words for m in re.finditer(re.escape(word), text_lower)]
        contexts = []

        for pos in positions:
            start = max(pos - context_size, 0)
            end = min(pos + context_size, len(text))
            snippet = text[start:end]
            for word in query_words:
                snippet = re.sub(re.escape(word), colored(word, 'red'), snippet, flags=re.IGNORECASE)
            contexts.append(snippet)

        return ' ... '.join(contexts)

