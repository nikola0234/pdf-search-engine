import pickle

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.pages = []

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word, page_num):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        if page_num not in node.pages:
            node.pages.append(page_num)

    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return []
            node = node.children[char]
        return node.pages if node.is_end_of_word else []

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state
