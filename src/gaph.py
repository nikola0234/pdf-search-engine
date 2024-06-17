class GraphNode:
    def __init__(self, page_num):
        self.page_num = page_num
        self.edges = []
        self.rank = 1.0

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

    def calculate_page_rank(self, iterations=20, d=0.85):
        num_nodes = len(self.nodes)
        if num_nodes == 0:
            return

        for node in self.nodes.values():
            node.rank = 1.0 / num_nodes

        for _ in range(iterations):
            new_ranks = {}
            for node in self.nodes.values():
                rank_sum = sum(neighbor.rank / len(neighbor.edges) for neighbor in node.edges if neighbor.edges)
                new_ranks[node.page_num] = (1 - d) / num_nodes + d * rank_sum

            for page_num, new_rank in new_ranks.items():
                self.nodes[page_num].rank = new_rank

    def __repr__(self):
        return f"Graph with {len(self.nodes)} nodes"
