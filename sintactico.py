from lexico import TokenType
from arbol_sintaxis import ASTNode


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

    def error(self, msg):
        token = self.current_token()
        if token:
            self.errors.append(f"[Línea {token.line}, Columna {token.column}] Error: {msg}")
        else:
            self.errors.append(f"[EOF] Error: {msg}")

    def parse(self):
        self.errors = []
        root = ASTNode("programa")
        try:
            prog = self.programa()
            if prog:
                root.agregar_hijo(prog)
        except Exception as e:
            self.error(f"Error inesperado: {str(e)}")
        return root, self.errors



    def programa(self):
        node = ASTNode("programa")

        if not self.match("RESERVED_WORD", "main"):
            self.error("Se esperaba 'main'")
            return node
        node.agregar_hijo(ASTNode("main"))

        if not self.match("SYMBOL", "{"):
            self.error("Se esperaba '{'")
            return node

        node.agregar_hijo(self.lista_declaracion())

        if not self.match("SYMBOL", "}"):
            self.error("Se esperaba '}'")
        return node

    def lista_declaracion(self):
        node = ASTNode("lista_declaracion")
        prev_index = -1

        while self.index < len(self.tokens) and self.index != prev_index:
            prev_index = self.index
            current = self.current_token()
            if not current or current.value == "}":
                break

            try:
                decl = self.declaracion()
                if decl:
                    node.agregar_hijo(decl)
            except Exception as e:
                self.error(f"No se pudo analizar la instrucción en línea {current.line}: {str(e)}")
                self.index += 1  # sigue avanzando incluso con error

        return node



    def declaracion(self):
        token = self.current_token()
        if token and token.value in ["int", "float", "bool"]:
            return self.declaracion_variable()
        else:
            return self.sentencia()

    def declaracion_variable(self):
        node = ASTNode("declaracion_variable")

        tipo = self.match("RESERVED_WORD")
        if tipo and tipo.value in ["int", "float", "bool"]:
            tipo_node = ASTNode(tipo.value.upper(), tipo.value.upper(), tipo.line, tipo.column)  # <-- aquí el tipo va en node_type
            node.agregar_hijo(tipo_node)
        else:
            self.error("Se esperaba un tipo de dato")
            return node

        while True:
            id_token = self.match("IDENTIFIER")
            if id_token:
                id_node = ASTNode(f"ID ({id_token.value})", "ID", id_token.line, id_token.column)  # <-- aquí también
                node.agregar_hijo(id_node)
            else:
                self.error("Se esperaba un identificador")
                break

            if not self.match("SYMBOL", ","):
                break

        if not self.match("SYMBOL", ";"):
            self.error("Se esperaba ';' al final de la declaración")

        return node


    def sentencia_if(self):
        token_if = self.match("RESERVED_WORD", "if")
        nodo_if = ASTNode("if", "if", token_if.line, token_if.column)

        if not self.match("SYMBOL", "("):
            self.error("Se esperaba '(' después de 'if'")
            

        condicion = self.expresion()
        if condicion:
            nodo_if.agregar_hijo(condicion)
        else:
            self.error("Condición inválida en 'if'")

        if not self.match("SYMBOL", ")"):
            self.error("Se esperaba ')' después de la condición")

        cuerpo = self.bloque_sentencias() or self.sentencia()
        if cuerpo:
            nodo_if.agregar_hijo(cuerpo)

        if self.match("RESERVED_WORD", "else"):
            else_node = ASTNode("else")
            sentencia_else = self.sentencia()
            if sentencia_else:
                else_node.agregar_hijo(sentencia_else)
            nodo_if.agregar_hijo(else_node)

        return nodo_if

    def sentencia_while(self):
        token_while = self.match("RESERVED_WORD", "while")
        nodo_while = ASTNode("while", "while", token_while.line, token_while.column)

        if not self.match("SYMBOL", "("):
            self.error("Se esperaba '(' después de 'while'")
            

        condicion = self.expresion()
        if condicion:
            nodo_while.agregar_hijo(condicion)

        if not self.match("SYMBOL", ")"):
            self.error("Se esperaba ')' después de la condición de 'while'")

        cuerpo = self.bloque_sentencias() or self.sentencia()
        if cuerpo:
            nodo_while.agregar_hijo(cuerpo)

        return nodo_while
    
    def sentencia_dowhile(self):
        token_do = self.match("RESERVED_WORD", "do")
        nodo_do = ASTNode("do-while", "ciclo", token_do.line if token_do else 0, token_do.column if token_do else 0)

        cuerpo = self.bloque_sentencias()
        if cuerpo:
            nodo_do.agregar_hijo(cuerpo)
        else:
            self.error("Bloque faltante en 'do'")

        if not self.match("RESERVED_WORD", "until"):
            self.error("Se esperaba 'until' después del bloque 'do'")
            return nodo_do

        condicion = self.expresion()
        if condicion:
            nodo_do.agregar_hijo(condicion)
        else:
            self.error("Condición inválida en 'until'")

        return nodo_do



    def sentencia_incremento(self):
        token = self.match("INCREMENT") or self.match("DECREMENT")
        if token:
            tipo_op = token.type.name

            # Nodo principal: "incremento" o "decremento"
            nombre_nodo = "incremento" if tipo_op == "INCREMENT" else "decremento"
            nodo_inc = ASTNode(nombre_nodo.upper(), tipo_op, token.line, token.column)

            id_token = self.match("IDENTIFIER")
            if id_token:
                # ID original del incremento
                nodo_id = ASTNode(f"ID ({id_token.value})", "ID", id_token.line, id_token.column)
                nodo_inc.agregar_hijo(nodo_id)

                # Nodo de asignación explícito
                nodo_asig = ASTNode("asignacion_por_incremento", "ASIGNACION", id_token.line, id_token.column)
                nodo_asig.agregar_hijo(ASTNode(f"ID ({id_token.value})", "ID", id_token.line, id_token.column))

                # Operador suma o resta
                operador = "+" if tipo_op == "INCREMENT" else "-"
                operador_node = ASTNode(operador, "ARITHMETIC_OP", id_token.line, id_token.column)

                # a = a + 1
                operador_node.agregar_hijo(ASTNode(f"ID ({id_token.value})", "ID", id_token.line, id_token.column))
                operador_node.agregar_hijo(ASTNode("NUM (1)", "NUM", id_token.line, id_token.column))

                nodo_asig.agregar_hijo(operador_node)
                nodo_inc.agregar_hijo(nodo_asig)
            else:
                self.error("Se esperaba un identificador después de '++' o '--'")

            punto_y_coma = self.match("SYMBOL", ";")
            if punto_y_coma:
                nodo_inc.agregar_hijo(ASTNode("SYMBOL (;)", "SYMBOL", punto_y_coma.line, punto_y_coma.column))
            else:
                self.error("Se esperaba ';' al final del incremento/decremento")

            return nodo_inc
        return None







    def sentencia_io(self):
        token = self.match("RESERVED_WORD")
        if not token or token.value not in ["cin", "cout"]:
            self.error("Se esperaba 'cin' o 'cout'")
            return None

        nodo_io = ASTNode(token.value, token.value.upper(), token.line, token.column)

        if not self.match("ARITHMETIC_OP"):  # >>
            self.error("Se esperaba operador '>>' o '<<'")
            return nodo_io

        id_token = self.match("IDENTIFIER")
        if id_token:
            nodo_io.agregar_hijo(ASTNode(f"ID ({id_token.value})", "ID", id_token.line, id_token.column))
        else:
            self.error("Se esperaba un identificador después de 'cin' o 'cout'")

        if not self.match("SYMBOL", ";"):
            self.error("Se esperaba ';' al final de la sentencia de E/S")

        return nodo_io



    def sentencia(self):
        token = self.current_token()
        if token is None:
            return None

        if token.value == "end":
            # Consumir 'end' y continuar sin generar nodo
            self.match("RESERVED_WORD", "end")
            return None

        if token.type.name == "IDENTIFIER":
            return self.sentencia_asignacion()
        if token.value == "if":
            return self.sentencia_if_then()
        if token.value == "while":
            return self.sentencia_while()
        if token.value == "do":
            return self.sentencia_dowhile()
        if token.type.name in ["INCREMENT", "DECREMENT"]:
            return self.sentencia_incremento()
        if token.value in ["cin", "cout"]:
            return self.sentencia_io()

        self.error(f"Sentencia no reconocida: {token.value}")
        token = self.current_token()
        self.index += 1
        return ASTNode(f"ERROR ({token.value})", "ERROR", token.line, token.column)



    def sentencia_if_then(self):
        token_if = self.match("RESERVED_WORD", "if")
        nodo_if = ASTNode("if", "if", token_if.line, token_if.column)

        condicion = self.expresion()
        if not condicion:
            self.error("Condición inválida en 'if'")
            return nodo_if
        nodo_if.agregar_hijo(condicion)

        if not self.match("RESERVED_WORD", "then"):
            self.error("Se esperaba 'then' después de la condición")

        cuerpo = self.sentencia() or self.bloque_sentencias()
        if cuerpo:
            nodo_if.agregar_hijo(cuerpo)

        if self.match("RESERVED_WORD", "else"):
            else_node = ASTNode("else")
            cuerpo_else = self.sentencia() or self.bloque_sentencias()
            if cuerpo_else:
                else_node.agregar_hijo(cuerpo_else)
            nodo_if.agregar_hijo(else_node)

        if not self.match("RESERVED_WORD", "end"):
            self.error("Se esperaba 'end' para cerrar el 'if'")
        
        return nodo_if



    def expresion(self):
        return self.expresion_binaria()

    def expresion_binaria(self):
        izquierda = self.expresion_primaria()
        if not izquierda:
            return None

        while True:
            token = self.current_token()
            if token and token.type.name in ["ARITHMETIC_OP", "RELATIONAL_OP", "LOGICAL_OP"]:
                operador_token = self.match(token.type.name)  # CORREGIDO AQUÍ
                derecha = self.expresion_primaria()
                if not derecha:
                    self.error("Se esperaba un operando después del operador")
                    break

                operador_node = ASTNode(f"{operador_token.value}", operador_token.type.name, operador_token.line, operador_token.column)
                operador_node.agregar_hijo(izquierda)
                operador_node.agregar_hijo(derecha)
                izquierda = operador_node
            else:
                break

        return izquierda


    def expresion_primaria(self):
        token = self.current_token()

        # Manejar paréntesis
        if token and token.type.name == "SYMBOL" and token.value == "(":
            self.match("SYMBOL", "(")
            nodo = self.expresion()
            if not self.match("SYMBOL", ")"):
                self.error("Se esperaba ')' al final de la subexpresión")
            return nodo

        # Manejar flotantes
        if token and token.type.name == "DECIMAL":
            node = ASTNode(f"FLOATNUM ({token.value})", "FLOATNUM", token.line, token.column)
            self.index += 1
            return node

        # Manejar enteros
        if token and token.type.name == "INTEGER":
            node = ASTNode(f"NUM ({token.value})", "NUM", token.line, token.column)
            self.index += 1
            return node

        # Manejar identificadores
        if token and token.type.name == "IDENTIFIER":
            node = ASTNode(f"ID ({token.value})", "ID", token.line, token.column)
            self.index += 1
            return node

        self.error("Se esperaba un operando")
        return None





    def sentencia_asignacion(self):
        id_token = self.match("IDENTIFIER")
        nodo_asignacion = ASTNode("ASIGNACION", "ASIGNACION", id_token.line if id_token else 0, id_token.column if id_token else 0)

        if id_token:
            nodo_asignacion.agregar_hijo(ASTNode(f"ID ({id_token.value})", "ID", id_token.line, id_token.column))
        else:
            self.error("Se esperaba un identificador al inicio de la asignación")

        if not self.match("ASSIGNMENT"):
            self.error("Se esperaba '='")
            return nodo_asignacion

        expr = self.expresion()
        if expr:
            nodo_asignacion.agregar_hijo(expr)
        else:
            self.error("Expresión inválida en asignación")

        self.match("SYMBOL", ";")  # Si no hay ';' lo ignoramos pero continuamos
        return nodo_asignacion




    def ciclo_dowhile(self):
        if self.verificar('RESERVED_WORD', 'do'):
            nodo_do = ASTNode("do-while", "ciclo", self.actual.line, self.actual.column)
            self.avanzar()

            bloque = self.bloque_sentencias()
            if bloque:
                nodo_do.agregar_hijo(bloque)

            if self.verificar('RESERVED_WORD', 'until'):
                self.avanzar()

                if self.verificar('SYMBOL', '('):
                    self.avanzar()
                    expr = self.expresion()

                    if expr:
                        nodo_do.agregar_hijo(expr)

                        if self.verificar('SYMBOL', ')'):
                            self.avanzar()

                            if self.verificar('SYMBOL', ';'):
                                self.avanzar()
                                return nodo_do
                            else:
                                self.error("Se esperaba ';' después del until")
                        else:
                            self.error("Se esperaba ')' en la condición de until")
                    else:
                        self.error("Condición inválida en until")
                else:
                    self.error("Se esperaba '(' después de until")
            else:
                self.error("Se esperaba 'until' después del bloque do")

    
    def bloque_sentencias(self):
        # Acepta '{' o 'begin' o incluso sin nada explícito si ya estás dentro de un bloque
        if self.current_token() and self.current_token().value == "{":
            self.match("SYMBOL", "{")
            cierre = "}"
        elif self.current_token() and self.current_token().value == "begin":
            self.match("RESERVED_WORD", "begin")
            cierre = "end"
        else:
            cierre = "end"  # Por defecto, considera 'end' como cierre válido

        nodo_bloque = ASTNode("bloque")

        while self.index < len(self.tokens):
            token = self.current_token()
            if token and token.value == cierre:
                self.match(token.type.name, cierre)
                break

            sentencia = self.sentencia()
            if sentencia:
                nodo_bloque.agregar_hijo(sentencia)
            else:
                self.index += 1  # evitar loop infinito si hay error

        return nodo_bloque


    def sentencia_dountil(self):
        token_do = self.match("RESERVED_WORD", "do")
        nodo_do = ASTNode("do-until", "ciclo", token_do.line if token_do else 0, token_do.column if token_do else 0)

        # Analizar bloque de sentencias del cuerpo del do
        cuerpo = self.bloque_sentencias() or self.sentencia()
        if cuerpo:
            nodo_do.agregar_hijo(cuerpo)
        else:
            self.error("Se esperaba el cuerpo del ciclo 'do'")

        if not self.match("RESERVED_WORD", "until"):
            self.error("Se esperaba 'until' después del bloque 'do'")
            return nodo_do

        condicion = self.expresion()
        if condicion:
            nodo_do.agregar_hijo(condicion)
        else:
            self.error("Condición inválida en 'until'")

        return nodo_do
