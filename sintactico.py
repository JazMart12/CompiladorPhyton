# sintactico.py

from lexico import TokenType
from arbol_sintaxis import ASTNode, NodeType

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0
        self.errors = []

    def current_token(self):
        if self.index < len(self.tokens):
            return self.tokens[self.index]
        return None

    def match(self, expected_type, expected_value=None):
        token = self.current_token()
        if token and token.type.name == expected_type:
            if expected_value is None or token.value == expected_value:
                self.index += 1
                return token
        return None

    def consume(self):
        token = self.current_token()
        if token:
            self.index += 1
        return token

    def is_at_end(self):
        return self.index >= len(self.tokens)

    def error(self, message, token=None):
        token = token or self.current_token()
        if token:
            self.errors.append(f"Error sintáctico en línea {token.line}, columna {token.column}: {message}")
        else:
            self.errors.append(f"Error sintáctico: {message}")

    def parse(self):
        ast = self.parse_programa()
        return ast, self.errors

    def parse_programa(self):
        token = self.match("RESERVED_WORD", "main")
        if not token:
            self.error("Se esperaba 'main'")
            return None

        main_node = ASTNode("main", NodeType.MAIN, token.line, token.column)

        if not self.match("SYMBOL", "{"):
            self.error("Se esperaba '{'")
            return main_node

        main_node.add_child(self.parse_lista_declaracion())

        if not self.match("SYMBOL", "}"):
            self.error("Se esperaba '}'")
        return main_node

    def parse_lista_declaracion(self):
        node = ASTNode("Lista Declaraciones", NodeType.LISTA)
        while not self.is_at_end() and self.current_token().value != "}":
            decl = self.parse_declaracion()
            if decl:
                node.add_child(decl)
            else:
                self.consume()
        return node

    def parse_declaracion(self):
        token = self.current_token()
        if token and token.type == TokenType.RESERVED_WORD and token.value in ["int", "float", "bool"]:
            return self.parse_declaracion_variable()
        else:
            return self.parse_lista_sentencias()

    def parse_declaracion_variable(self):
        tipo_token = self.consume()
        tipo_node = ASTNode(tipo_token.value, NodeType.TIPO, tipo_token.line, tipo_token.column)
        id_token = self.match("IDENTIFIER")
        if not id_token:
            self.error("Se esperaba identificador")
            return tipo_node
        tipo_node.add_child(ASTNode(id_token.value, NodeType.IDENTIFICADOR, id_token.line, id_token.column))

        while self.match("SYMBOL", ","):
            next_id = self.match("IDENTIFIER")
            if next_id:
                tipo_node.add_child(ASTNode(next_id.value, NodeType.IDENTIFICADOR, next_id.line, next_id.column))
            else:
                self.error("Se esperaba identificador después de ','")

        if not self.match("SYMBOL", ";"):
            self.error("Se esperaba ';'")
        return tipo_node

    def parse_lista_sentencias(self):
        node = ASTNode("Lista Sentencias", NodeType.LISTA)
        while not self.is_at_end() and self.current_token().value not in ["}", "end"]:
            stmt = self.parse_sentencia()
            if stmt:
                node.add_child(stmt)
            else:
                self.consume()
        return node

    def parse_sentencia(self):
        token = self.current_token()
        if not token:
           return None

        if token.value == "if":
         return self.parse_if()
        elif token.value == "while":
         return self.parse_while()
        elif token.value == "do":
         return self.parse_do()
        elif token.value == "cin":
         return self.parse_entrada()
        elif token.value == "cout":
         return self.parse_salida()
        elif token.type == TokenType.IDENTIFIER:
        # Detectar si es incremento o decremento (ej. a++; o b--; )
         if self.index + 1 < len(self.tokens):
             next_token = self.tokens[self.index + 1]
             if next_token.type in [TokenType.INCREMENT, TokenType.DECREMENT]:
                id_token = self.consume()
                op_token = self.consume()

                # Nodo raíz de la asignación
                assign_node = ASTNode("=", NodeType.ASIGNACION, op_token.line, op_token.column)

                # Nodo ID izquierdo
                id_izq = ASTNode(id_token.value, NodeType.IDENTIFICADOR, id_token.line, id_token.column)
                assign_node.add_child(id_izq)

                # Nodo de operación: + o -
                op_value = "+" if op_token.type == TokenType.INCREMENT else "-"
                tipo_op = NodeType.SUMA if op_value == "+" else NodeType.RESTA
                op_node = ASTNode(op_value, tipo_op, op_token.line, op_token.column)


                # Operando izquierdo: ID original
                op_node.add_child(ASTNode(id_token.value, NodeType.IDENTIFICADOR, id_token.line, id_token.column))
                # Operando derecho: constante 1
                op_node.add_child(ASTNode("1", NodeType.FACTOR, op_token.line, op_token.column))

                # Añadir la expresión al nodo de asignación
                assign_node.add_child(op_node)

                self.match("SYMBOL", ";")
                return assign_node

        # Si no es incremento ni decremento, procesar como asignación normal
         return self.parse_asignacion()
        else:
            self.error("Sentencia no válida", token)
            return None


        




    def parse_asignacion(self):
        id_token = self.match("IDENTIFIER")
        assign_token = self.match("ASSIGNMENT")
        if not assign_token:
            self.error("Se esperaba '=' en asignación")
            return None
        assign_node = ASTNode("Asignación", NodeType.ASIGNACION, assign_token.line, assign_token.column)
        assign_node.add_child(ASTNode(id_token.value, NodeType.IDENTIFICADOR, id_token.line, id_token.column))

        if self.current_token().type == TokenType.SYMBOL and self.current_token().value == ";":
            self.match("SYMBOL", ";")  # asignación vacía
            return assign_node

        expr = self.parse_expresion()
        if expr:
            assign_node.add_child(expr)

        if not self.match("SYMBOL", ";"):
            self.error("Falta ';' al final de asignación")
        return assign_node

    def parse_if(self):
        if_token = self.consume()
        node = ASTNode("if", NodeType.IF, if_token.line, if_token.column)
        node.add_child(self.parse_expresion())

        if not self.match("RESERVED_WORD", "then"):
            self.error("Falta 'then' en if")

        node.add_child(self.parse_lista_sentencias())

        if self.match("RESERVED_WORD", "else"):
            node.add_child(self.parse_lista_sentencias())

        if not self.match("RESERVED_WORD", "end"):
            self.error("Falta 'end' al cerrar if")
        return node

    def parse_while(self):
        while_token = self.consume()
        node = ASTNode("while", NodeType.WHILE, while_token.line, while_token.column)
        node.add_child(self.parse_expresion())
        node.add_child(self.parse_lista_sentencias())
        if not self.match("RESERVED_WORD", "end"):
            self.error("Falta 'end' en while")
        return node

    def parse_do(self):
        do_token = self.consume()
        node = ASTNode("do", NodeType.DO, do_token.line, do_token.column)
        node.add_child(self.parse_lista_sentencias())
        if not self.match("RESERVED_WORD", "while"):
            self.error("Falta 'while' en estructura do")
        node.add_child(self.parse_expresion())
        return node

    def parse_entrada(self):
        cin_token = self.consume()
        node = ASTNode("cin", NodeType.INPUT, cin_token.line, cin_token.column)
        if not self.match("ARITHMETIC_OP", ">>"):
            self.error("Falta '>>' en cin")
            return node
        id_token = self.match("IDENTIFIER")
        if id_token:
            node.add_child(ASTNode(id_token.value, NodeType.IDENTIFICADOR, id_token.line, id_token.column))
        else:
            self.error("Falta identificador en cin")
        self.match("SYMBOL", ";")
        return node

    def parse_salida(self):
        cout_token = self.consume()
        node = ASTNode("cout", NodeType.OUTPUT, cout_token.line, cout_token.column)
        if not self.match("ARITHMETIC_OP", "<<"):
            self.error("Falta '<<' en cout")
            return node
        salida = self.parse_salida_valor()
        if salida:
            node.add_child(salida)
        self.match("SYMBOL", ";")
        return node

    def parse_salida_valor(self):
        token = self.current_token()
        if token.type == TokenType.STRING:
            self.consume()
            return ASTNode(token.value, NodeType.CADENA, token.line, token.column)
        else:
            return self.parse_expresion()

    def parse_expresion(self):
        left = self.parse_expresion_simple()
        token = self.current_token()
        if token and token.type == TokenType.RELATIONAL_OP:
            op_token = self.consume()
            op_node = ASTNode(op_token.value, NodeType.RELACIONAL, op_token.line, op_token.column)
            op_node.add_child(left)
            right = self.parse_expresion_simple()
            if right:
                op_node.add_child(right)
            return op_node
        return left

    def parse_expresion_simple(self):
        node = self.parse_termino()
        while not self.is_at_end():
            token = self.current_token()
            if token.type == TokenType.ARITHMETIC_OP and token.value in ["+", "-"]:
                op_token = self.consume()
                tipo = NodeType.SUMA if op_token.value == "+" else NodeType.RESTA
                op_node = ASTNode(op_token.value, tipo, op_token.line, op_token.column)
                op_node.add_child(node)
                op_node.add_child(self.parse_termino())
                node = op_node
            elif token.type in [TokenType.INCREMENT, TokenType.DECREMENT]:
                op_token = self.consume()
                tipo = NodeType.INCREMENTO if op_token.type == TokenType.INCREMENT else NodeType.DECREMENTO
                op_node = ASTNode(op_token.value, tipo, op_token.line, op_token.column)
                op_node.add_child(node)
                node = op_node
            else:
                break
        return node
    


    def parse_termino(self):
        node = self.parse_factor()
        while not self.is_at_end():
            token = self.current_token()
            if token.type == TokenType.ARITHMETIC_OP and token.value in ["*", "/", "%"]:
                op_token = self.consume()
                op_node = ASTNode(op_token.value, NodeType.MULTIPLICACION, op_token.line, op_token.column)
                op_node.add_child(node)
                op_node.add_child(self.parse_factor())
                node = op_node
            else:
                break
        return node

    def parse_factor(self):
        node = self.parse_componente()
        while not self.is_at_end():
            token = self.current_token()
            if token.type == TokenType.ARITHMETIC_OP and token.value == "^":
                op_token = self.consume()
                op_node = ASTNode("^", NodeType.POTENCIA, op_token.line, op_token.column)
                op_node.add_child(node)
                op_node.add_child(self.parse_componente())
                node = op_node
            else:
                break
        return node

    def parse_componente(self):
        token = self.current_token()
        if token is None:
            return None

        if token.type == TokenType.SYMBOL and token.value == "(":
            self.consume()
            expr = self.parse_expresion()
            self.match("SYMBOL", ")")
            return expr
        elif token.type == TokenType.INTEGER or token.type == TokenType.DECIMAL:
            self.consume()
            return ASTNode(token.value, NodeType.FACTOR, token.line, token.column)
        elif token.type == TokenType.IDENTIFIER:
            self.consume()
            return ASTNode(token.value, NodeType.IDENTIFICADOR, token.line, token.column)
        elif token.type == TokenType.RESERVED_WORD and token.value in ["true", "false"]:
            self.consume()
            return ASTNode(token.value, NodeType.FACTOR, token.line, token.column)
        elif token.type == TokenType.LOGICAL_OP or token.value == "!":
            op = self.consume()
            op_node = ASTNode(op.value, NodeType.LOGICO, op.line, op.column)
            op_node.add_child(self.parse_componente())
            return op_node
        else:
            self.error("Componente inválido", token)
            self.consume()
            return None