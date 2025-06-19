# arbol_sintaxis.py

from enum import Enum

class NodeType(Enum):
    PROGRAMA = "Programa"
    DECLARACION = "Declaración"
    TIPO = "Tipo"
    IDENTIFICADOR = "Identificador"
    SENTENCIA = "Sentencia"
    ASIGNACION = "Asignación"
    EXPRESION = "Expresión"
    EXPRESION_SIMPLE = "Expresión Simple"
    TERMINO = "Término"
    FACTOR = "Factor"
    COMPONENTE = "Componente"
    OPERADOR = "Operador"
    IF = "If"
    WHILE = "While"
    DO = "Do"
    INPUT = "Entrada"
    OUTPUT = "Salida"
    RELACIONAL = "Relacional"
    SUMA = "Suma"
    RESTA = "Resta"
    MULTIPLICACION = "Multiplicación"
    POTENCIA = "Potencia"
    LOGICO = "Lógico"
    INCREMENTO = "Incremento"
    DECREMENTO = "Decremento"
    CADENA = "Cadena"
    LISTA = "Lista"
    MAIN = "Main"
    ERROR = "Error"

class ASTNode:
    def __init__(self, name, node_type, line=None, column=None):
        self.name = name                  # Texto del nodo (ej. '+', 'if', 'id', 'int')
        self.node_type = node_type        # Tipo de nodo (NodeType)
        self.line = line                  # Línea en el código fuente
        self.column = column              # Columna en el código fuente
        self.children = []                # Lista de hijos (nodos AST)

    def add_child(self, child_node):
        if child_node:
            self.children.append(child_node)

    def __repr__(self):
        return f"{self.node_type.name}('{self.name}') [{self.line}:{self.column}]"

    def to_dict(self):
        """Convierte el nodo a un diccionario para visualización"""
        return {
            "name": self.name,
            "type": self.node_type.name,
            "line": self.line,
            "column": self.column,
            "children": [child.to_dict() for child in self.children]
        }