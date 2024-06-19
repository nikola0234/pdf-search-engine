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
    
    def get_trie(self):
        return self.trie


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

    def calculate_page_rank(self):
        self.graph.calculate_page_rank()

    def search_and(self, term1, term2):
        pages1 = set(self.trie.search_log(term1))
        pages2 = set(self.trie.search_log(term2))
        return pages1 & pages2

    def search_or(self, term1, term2):
        pages1 = set(self.trie.search_log(term1))
        pages2 = set(self.trie.search_log(term2))
        return pages1 | pages2

    def search_not(self, term1, term2):
        pages1 = set(self.trie.search_log(term1))
        pages_to_exclude = set()
        term2_regex = re.compile(r'\b' + re.escape(term2) + r'\b', re.IGNORECASE)

        for page_num in pages1:
            if term2_regex.search(self.pages_text[page_num]):
                pages_to_exclude.add(page_num)

        return pages1 - pages_to_exclude
    
    
    def evaluate_expression(self, query):
        def parse_expression(query):
            tokens = re.findall(r'\(|\)|\w+|AND|OR|NOT', query)
            return tokens

        def eval_expression(tokens):
            stack = []
            operators = []

            def apply_operator():
                operator = operators.pop()
                right = stack.pop()
                left = stack.pop() if stack else None

                if operator == 'AND':
                    stack.append(self.search_and(left, right))
                elif operator == 'OR':
                    stack.append(self.search_or(left, right))
                elif operator == 'NOT':
                    stack.append(self.search_not(left, right))

            for token in tokens:
                if token == '(':
                    operators.append(token)
                elif token == ')':
                    while operators and operators[-1] != '(':
                        apply_operator()
                    operators.pop()
                elif token in {'AND', 'OR', 'NOT'}:
                    while (operators and operators[-1] in {'AND', 'OR', 'NOT'} and
                        (token != 'NOT' or operators[-1] == 'NOT')):
                        apply_operator()
                    operators.append(token)
                else:
                    stack.append(token.lower())

            while operators:
                apply_operator()

            return stack[0] if stack else set()

        tokens = parse_expression(query)
        result_pages = eval_expression(tokens)
        return result_pages

    def evaluate_expression1(self, query):
        def parse_expression(query):
            
            tokens = re.findall(r'\(|\)|\w+|AND|OR|NOT', query)
            return tokens

        def eval_expression(tokens):
            def apply_operator(operators, values):
                operator = operators.pop()
                if operator == 'NOT':
                    value = values.pop()
                    values.append(self.search_not1(value))
                else:
                    right = values.pop()
                    left = values.pop()
                    if operator == 'AND':
                        values.append(self.search_and1(left, right))
                    elif operator == 'OR':
                        values.append(self.search_or1(left, right))

            values = []
            operators = []
            precedence = {'OR': 1, 'AND': 2, 'NOT': 3}
            i = 0
            while i < len(tokens):
                token = tokens[i]
                if token == '(':
                    operators.append(token)
                elif token == ')':
                    while operators and operators[-1] != '(':
                        apply_operator(operators, values)
                    operators.pop()  
                elif token in precedence:
                    while (operators and operators[-1] in precedence and
                        precedence[token] <= precedence[operators[-1]]):
                        apply_operator(operators, values)
                    operators.append(token)
                else:
                    values.append(token)
                i += 1

            while operators:
                apply_operator(operators, values)

            return values[0]

        tokens = parse_expression(query)
        result_pages = eval_expression(tokens)
        return result_pages

    def search_log1(self, query):
        result_pages = self.evaluate_expression(query)
        query_terms = [term for term in re.findall(r'\w+', query.lower()) if term not in {'and', 'or', 'not'}]

        results = {}
        for page_num in result_pages:
            results[page_num] = {
                'count': sum(self.pages_text[page_num].lower().count(term) for term in query_terms),
                'rank': self.graph.get_node(page_num).rank
            }

        sorted_results = sorted(results.items(), key=lambda item: (item[1]['count'], item[1]['rank']), reverse=True)
        search_results = []

        for i, (page_num, info) in enumerate(sorted_results):
            context = self.get_context(self.pages_text[page_num], query_terms)
            search_results.append((i + 1, page_num + 1, context))

        return search_results

    def search_and1(self, term1, term2):
        if isinstance(term1, set):
            pages1 = term1
        else:
            pages1 = set(self.trie.search(term1))
        if isinstance(term2, set):
            pages2 = term2
        else:
            pages2 = set(self.trie.search(term2))
        return pages1 & pages2

    def search_or1(self, term1, term2):
        if isinstance(term1, set):
            pages1 = term1
        else:
            pages1 = set(self.trie.search(term1))
        if isinstance(term2, set):
            pages2 = term2
        else:
            pages2 = set(self.trie.search(term2))
        return pages1 | pages2

    def search_not1(self, term1, term2=None):
        if isinstance(term1, set):
            pages1 = term1
        else:
            pages1 = set(self.trie.search(term1))
        if term2 is None:
            return set(range(len(self.pages_text))) - pages1
        else:
            if isinstance(term2, set):
                pages2 = term2
            else:
                pages2 = set(self.trie.search(term2))
            return pages1 - pages2


    def search_log(self, query):
        result_pages = self.evaluate_expression(query)
        query_terms = [term for term in re.findall(r'\w+', query.lower()) if term not in {'and', 'or', 'not'}]

        results = {}
        for page_num in result_pages:
            results[page_num] = {'count': sum(self.pages_text[page_num].lower().count(term) for term in query_terms), 'rank': self.graph.get_node(page_num).rank}

        sorted_results = sorted(results.items(), key=lambda item: (item[1]['count'], item[1]['rank']), reverse=True)
        search_results = []

        for i, (page_num, info) in enumerate(sorted_results):
            context = self.get_context(self.pages_text[page_num], query_terms)
            search_results.append((i + 1, page_num + 1, context))

        return search_results
    
    
    def search(self, query):
        if not self.is_indexed:
            raise ValueError("Index not built or loaded")
        
        if any(op in query for op in ['AND', 'OR', 'NOT']):
            return self.search_log1(query)
            
        query_words = query.lower().split()
        results = {}

        for word in query_words:
            pages = self.trie.search(word)
            for page_num in pages:
                if page_num not in results:
                    results[page_num] = {'count': 0, 'rank': self.graph.get_node(page_num).rank}
                results[page_num]['count'] += self.pages_text[page_num].lower().count(word)

        sorted_results = sorted(results.items(), key=lambda item: (item[1]['count'], item[1]['rank']), reverse=True)
        search_results = []

        for i, (page_num, info) in enumerate(sorted_results):
            context = self.get_context(self.pages_text[page_num], query_words)
            search_results.append((i + 1, page_num + 1, context))

        return search_results

    def get_context(self, text, query_words, context_size=30):
        text_lower = text.lower()
        positions = [m.start() for word in query_words for m in re.finditer(re.escape(word), text_lower)]
        contexts = []

        for pos in positions:
            start = max(pos - context_size, 0)
            end = min(pos + context_size + len(query_words[0]), len(text))
            snippet = text[start:end]
            for word in query_words:
                snippet = re.sub(re.escape(word), colored(word, 'red'), snippet, flags=re.IGNORECASE)
            contexts.append(snippet)

        return ' ... '.join(contexts)
    
    
    def read_page(self, page_num):
        if 0 <= page_num < len(self.pages_text):
            return self.pages_text[page_num]
        else:
            return "Invalid page number."