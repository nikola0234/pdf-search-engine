import re
import os
import PyPDF2
from trie import Trie
from termcolor import colored
import pickle
from gaph import Graph
from fuzzywuzzy import process
from collections import Counter
import fitz
import datetime


class PdfSearchEngine:
    def __init__(self, path, index_file):
        self.path = path
        self.index_file = index_file
        self.trie = Trie()
        self.graph = Graph()
        self.pages_text = []
        self.is_indexed = False
        self.popular_terms = self.load_popular_terms()
        self.output_folder = r"c:\Users\Nikola Bjelica\Desktop\pdf-search-engine\src\search_results"
    
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


    def load_popular_terms(self, filename='popular_terms.txt'):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f]
        except FileNotFoundError:
            return []

    def save_popular_terms(self, filename='popular_terms.txt', top_n=500):
        word_counter = Counter()
        
        for page_text in self.pages_text:
            words = re.findall(r'\b\w+\b', page_text.lower())
            word_counter.update(words)
        
        most_common_words = word_counter.most_common(top_n)
        
        with open(filename, 'w', encoding='utf-8') as f:
            for word, count in most_common_words:
                if len(word) > 3:    
                    f.write(f'{word}\n')

    def suggest_correction(self, query):
        query_terms = re.findall(r'\b\w+\b', query.lower())
        suggestions = []

        for term in query_terms:
            suggestion = process.extractOne(term, self.popular_terms)
            if suggestion[1] > 70:
                suggestions.append(suggestion[0])
        
        return " ".join(suggestions)
        

    def autocomplete(self, prefix):
        suggestions = process.extractBests(prefix, self.popular_terms)
        for suggestion in suggestions:
            if suggestion[0].startswith(prefix):
                return suggestion


    def generate_unique_filename(self, base_name, extension="pdf"):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_name}_{timestamp}.{extension}"
        filepath = os.path.join(self.output_folder, filename)
        return filepath


    def save_and_highlight_search_results(self, search_results, query_terms):
        output_filename = self.generate_unique_filename('search_results')
        output_pdf = fitz.open()

        for _, page_num, _ in search_results[:10]:
            input_pdf = fitz.open(self.path)
            output_pdf.insert_pdf(input_pdf, from_page=page_num - 1, to_page=page_num - 1)
            new_page = output_pdf[-1]

            for term in query_terms:
                term_instances = new_page.search_for(term)
                for inst in term_instances:
                    new_page.add_highlight_annot(inst)

        output_pdf.save(output_filename)
        output_pdf.close()
        return output_filename


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


    def evaluate_expression(self, query):
        def parse_expression(query):
            tokens = re.findall(r'\".*?\"|\(|\)|\w+|AND|OR|NOT', query)
            return tokens

        def eval_expression(tokens):
            def apply_operator(operators, values):
                operator = operators.pop()
                right = values.pop()
                left = values.pop() if values else None
                if operator == 'NOT':
                    values.append(self.search_not(left, right))
                elif operator == 'AND':
                    values.append(self.search_and(left, right))
                elif operator == 'OR':
                    values.append(self.search_or(left, right))

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
                    if token.startswith('"') and token.endswith('"'):
                        phrase = token[1:-1]
                        values.append(set(self.search_phrase(phrase)))
                    else:
                        values.append(set(self.trie.search(token.lower())))
                i += 1

            while operators:
                apply_operator(operators, values)

            return values[0]

        tokens = parse_expression(query)
        result_pages = eval_expression(tokens)
        return result_pages

    def search_log(self, query, page=1, search_per_page=10):
        result_pages = self.evaluate_expression(query)
        
        query_phrases = [phrase[1:-1] for phrase in re.findall(r'\".*?\"', query.lower())]
        query_terms = [term for term in re.findall(r'\b\w+\b', query.lower()) if term not in ['and', 'or', 'not'] 
                    and all(term not in phrase.split() for phrase in query_phrases)]
        
        results = {}
        for page_num in result_pages:
            total_count = sum(self.pages_text[page_num].lower().count(term) for term in query_terms)
            total_count += sum(self.pages_text[page_num].lower().count(phrase) for phrase in query_phrases)
            results[page_num] = {
                'count': total_count,
                'rank': self.graph.get_node(page_num).rank
            }
            
        sorted_results = sorted(results.items(), key=lambda item: (item[1]['count'], item[1]['rank']), reverse=True)
        search_results = []

        start = (page - 1) * search_per_page
        end = start + search_per_page
        paginated_results = sorted_results[start:end]

        for i, (page_num, info) in enumerate(paginated_results):
            context = self.get_context(self.pages_text[page_num], query_phrases +  query_terms)
            search_results.append((start + i + 1, page_num + 1, context))
        
        return search_results

    def search_phrase(self, phrase):
        words = phrase.lower()
        pages = []

        for page_num, text in enumerate(self.pages_text):
            if words in text.lower():
                pages.append(page_num)
        
        return pages
    
    def search_and(self, term1, term2):
        if isinstance(term1, set):
            pages1 = term1
        else:
            pages1 = set(self.trie.search(term1))
        if isinstance(term2, set):
            pages2 = term2
        else:
            pages2 = set(self.trie.search(term2))
        return pages1 & pages2
    

    def search_or(self, term1, term2):
        if isinstance(term1, set):
            pages1 = term1
        else:
            pages1 = set(self.trie.search(term1))
        if isinstance(term2, set):
            pages2 = term2
        else:
            pages2 = set(self.trie.search(term2))
        return pages1 | pages2
    

    def search_not(self, term1, term2):
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
    

    def search(self, query, page=1, search_per_page=10):
        if not self.is_indexed:
            raise ValueError("Index not built or loaded")
        
        for qu in query.split():
            try:    
                if '*' in qu:
                    if ")" in qu:
                        print("QU: ", qu)
                        autocomplete_word = self.autocomplete(qu[:-2])[0]
                        autocomplete_word += ')'
                    elif "(" in qu:
                        print("QU: ", qu)
                        qu1 = qu[1:]
                        autocomplete_word = self.autocomplete(qu1[:-1])[0]
                        autocomplete_word = '(' + autocomplete_word
                    elif qu.startswith('"'):
                        print("QU: ", qu)
                        autocomplete_word = self.autocomplete(qu[1:-1])[0]
                        autocomplete_word = '"' + autocomplete_word
                    elif qu.endswith('"'):
                        print("QU: ", qu)
                        autocomplete_word = self.autocomplete(qu[:-2])[0]
                        autocomplete_word += '"'
                    else:    
                        autocomplete_word = self.autocomplete(qu[:-1])[0]
                    print('\n' + '-' * 80)
                    print(f"Auto complete: {qu[:-1]} -> {autocomplete_word}")
                    query = query.replace(qu, autocomplete_word)
            except:
                print("No autocomplete suggestions found.")
        
        print("QUERY: ", query)
        
        if any(op in query for op in ['AND', 'OR', 'NOT']):
            return self.search_log(query, page, search_per_page)
        
            
        query_words = re.findall(r'\".*?\"|\w+', query.lower())
        results = {}

        for word in query_words:

            if word.startswith('"') and word.endswith('"'):
                word = word[1:-1]
                pages = self.search_phrase(word)

            else:
                pages = self.trie.search(word)
                
            for page_num in pages:
                if page_num not in results:
                    results[page_num] = {'count': 0, 'rank': self.graph.get_node(page_num).rank}
                results[page_num]['count'] += self.pages_text[page_num].lower().count(word)

        sorted_results = sorted(results.items(), key=lambda item: (item[1]['count'], item[1]['rank']), reverse=True)
        search_results = []

        start = (page - 1) * search_per_page
        end = start + search_per_page
        paginated_results = sorted_results[start:end]


        for i, (page_num, info) in enumerate(paginated_results):
            context = self.get_context(self.pages_text[page_num], query_words)
            search_results.append((start + i + 1, page_num + 1, context))

        return search_results

    def get_context(self, text, query_words, context_size=30):
        text_lower = text.lower()
        positions = []

    
        for word in query_words:
            word_escaped = re.escape(word.strip('"'))
            for match in re.finditer(word_escaped, text_lower):
                positions.append((match.start(), match.end(), word.strip('"')))

        contexts = []

        for start_pos, end_pos, word in sorted(positions):
            start = max(start_pos - context_size, 0)
            end = min(end_pos + context_size, len(text))
            snippet = text[start:end]
            snippet = re.sub(re.escape(word), colored(word, 'red'), snippet, flags=re.IGNORECASE)
            contexts.append(snippet)

        return ' ... '.join(contexts)

    
    def read_page(self, page_num):
        if 0 <= page_num < len(self.pages_text):
            return self.pages_text[page_num]
        else:
            return "Invalid page number."