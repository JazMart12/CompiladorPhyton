class ASTNode:
    def __init__(self, name, node_type="", line=0, column=0):
        self.name = name
        self.node_type = node_type
        self.line = line
        self.column = column
        self.children = []

    def agregar_hijo(self, nodo):
        self.children.append(nodo)
