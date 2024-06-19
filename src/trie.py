import unicodedata

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.pages = set() 

class Trie:
    def __init__(self):
        self.root = TrieNode()


    def normalize_text(self, text):
        return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii').lower()
    
    
    
    def insert(self, word, page_num):
        word = self.normalize_text(word)
        for i in range(len(word)):
            node = self.root
            for char in word[:i + 1]:
                if char not in node.children:
                    node.children[char] = TrieNode()
                node = node.children[char]
            node.is_end_of_word = True
            node.pages.add(page_num)
    

    def search(self, word):
        result_pages = set()

        def _search(node, prefix):
            if word in prefix:
                result_pages.update(node.pages)
            for char, child in node.children.items():
                _search(child, prefix + char)

        _search(self.root, "")
        return list(result_pages)
    
    def search_log(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return []
            node = node.children[char]
        return node.pages if node.is_end_of_word else []


    def print_trie(self):
        def _print_trie(node, word):
            if node.is_end_of_word:
                print(f"Word: {word}, Pages: {sorted(node.pages)}")
            for char, child in node.children.items():
                _print_trie(child, word + char)
        
        _print_trie(self.root, "")
