import ast
import graphviz

class ControlFlowGraphVisitor(ast.NodeVisitor):
    def __init__(self):
        self.graph = graphviz.Digraph()
        self.node_count = 0

    def add_node(self, node, label=None):
        if label is None:
            label = f"{type(node).__name__}"
        self.graph.node(str(self.node_count), label=label)
        self.node_count += 1
        return self.node_count - 1

    def add_edge(self, src, dest):
        self.graph.edge(str(src), str(dest))

    def generic_visit(self, node):
        parent = self.add_node(node)
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        child = self.visit(item)
                        self.add_edge(parent, child)
            elif isinstance(value, ast.AST):
                child = self.visit(value)
                self.add_edge(parent, child)
        return parent

def generate_flowchart(code):
    tree = ast.parse(code)
    cfg_visitor = ControlFlowGraphVisitor()
    cfg_visitor.visit(tree)
    return cfg_visitor.graph


with open('./target.py', 'r') as file:
    code = file.read()

flowchart = generate_flowchart(code)
flowchart.render('astFlow', format='svg', cleanup=True)
