class GraphNode:
    def __init__(self, page_num):
        self.page_num = page_num
        self.edges = []

    def add_edge(self, node):
        self.edges.append(node)

class Graph:
    def __init__(self):
        self.nodes = {}

    def add_node(self, page_num):
        if page_num not in self.nodes:
            self.nodes[page_num] = GraphNode(page_num)

    def add_edge(self, from_page, to_page):
        if from_page in self.nodes and to_page in self.nodes:
            self.nodes[from_page].add_edge(self.nodes[to_page])
    
    def get_node(self, page_num):
        return self.nodes.get(page_num)

    def __repr__(self):
        return f"Graph with {len(self.nodes)} nodes"
