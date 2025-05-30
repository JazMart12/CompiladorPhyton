import re
from enum import Enum

# Token types definition
class TokenType(Enum):

    NUMBER = 1          # Enteros y reales (con/sin signo)
    IDENTIFIER = 2      # Identificadores
    COMMENT = 3         # Comentarios
    RESERVED_WORD = 4   # Palabras reservadas
    ARITHMETIC_OP = 5   # Operadores aritméticos
    RELATIONAL_OP = 6   # Operadores relacionales
    LOGICAL_OP = 16      # Operadores lógicos (mismo color que relacionales)
    SYMBOL = 7         # Símbolos
    ASSIGNMENT = 8      # Asignación
    ERROR = 9           # Error léxico
    CHAR = 10           # Caracteres 
    STRING = 11         # Cadenas 
    INCREMENT = 12
    DECREMENT = 13
    INTEGER = 14        # Números enteros
    DECIMAL = 15        # Números con punto decimal




class Token:
    def __init__(self, token_type, value, line, column):
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column
    
    def __str__(self):
        return f"<{self.type.name}, '{self.value}', Line {self.line}, Column {self.column}>"

class LexicalAnalyzer:
    def __init__(self):
        # Definir palabras reservadas
        self.reserved_words = {
            'if', 'else', 'end', 'do', 'while', 'switch', 'case',
            'int', 'float', 'main', 'cin', 'cout', 'then', 'return',
            'break', 'continue', 'for', 'foreach', 'in', 'function',
            'string', 'char', 'bool', 'true', 'false', 'null', 'until'
        }
        
        # Definir patrones para los tokens
        self.token_patterns = [

            (r'[+-]?\d+\.(?!\d)', TokenType.ERROR), 

            (r'[+-]?\d+(\.\d+)?([eE][+-]?\d+)?', TokenType.NUMBER),

            # Comentarios de múltiples líneas
            (r'/\*[\s\S]*?\*/', TokenType.COMMENT),

            # Comentarios de una línea
            (r'//.*', TokenType.COMMENT),

            # ✅ Mueve este arriba para evitar conflicto con '|'
            (r'&&|\|\||!', TokenType.LOGICAL_OP),

            # Operadores aritméticos (deja esto después)
            (r'[+\-*/\^%]|[+]{2}|[-]{2}', TokenType.ARITHMETIC_OP),

            # Operadores relacionales
            (r'<=|>=|==|!=|<|>', TokenType.RELATIONAL_OP),

            # Símbolos
            (r'[(){},;]', TokenType.SYMBOL),

            # Asignación
            (r'=', TokenType.ASSIGNMENT),

            # Identificadores
            (r'[a-zA-Z][a-zA-Z0-9]*', TokenType.IDENTIFIER),

            # Cadenas de texto
            (r'"([^"\\]|\\.)*"', TokenType.STRING),

            # Caracteres
            (r"'(\\.|[^'\\])+'", TokenType.CHAR)
        ]
        
        # Compilar patrones
        self.patterns = [(re.compile(pattern), token_type) for pattern, token_type in self.token_patterns]
        
        # Definir estructuras esperadas para mejorar la detección de errores
        self.expected_structures = {
            'if': r'if\s*$$[^)]*$$\s*then',
            'while': r'while\s*$$[^)]*$$\s*\{',
            'do': r'do\s*\{[^}]*\}\s*until\s*$$[^)]*$$',
            'assignment': r'[a-zA-Z][a-zA-Z0-9]*\s*=\s*[^;]*;'
        }
        
        # Definir operadores que requieren operandos a ambos lados
        self.binary_operators = {'+', '-', '*', '/', '%', '^', '==', '!=', '<', '>', '<=', '>=', '&&', '||'}
        
        # Definir operadores unarios
        self.unary_operators = {'++', '--', '!'}

        # Definir pares de delimitadores
        self.delimiter_pairs = {
            '(': ')',
            '{': '}',
            '[': ']',
            '"': '"',
            "'": "'"
        }
    ##############################################################
    def analyze(self, code):
        tokens = []
        errors = []
        
        open_delimiters = []
        last_token_type = None
        last_token_value = None
        
        position = 0
        line_num = 1
        col_num = 1
        code_len = len(code)

        while position < code_len:
            # Ignorar espacios en blanco
            match = re.match(r'\s+', code[position:])
            if match:
                for char in match.group(0):
                    if char == '\n':
                        line_num += 1
                        col_num = 1
                    else:
                        col_num += 1
                position += match.end()
                continue

            token_found = False

            # Revisar secuencias de '++' y '+'
            if code[position] == '+':
                plus_count = 0
                temp_pos = position
                while temp_pos < code_len and code[temp_pos] == '+':
                    plus_count += 1
                    temp_pos += 1

                for i in range(plus_count // 2):
                   tokens.append(Token(TokenType.INCREMENT, '++', line_num, col_num + i * 2))
                   last_token_type = TokenType.INCREMENT
                   last_token_value = '++'

                if plus_count % 2 == 1:
                    tokens.append(Token(TokenType.ARITHMETIC_OP, '+', line_num, col_num + (plus_count - 1)))
                    last_token_type = TokenType.ARITHMETIC_OP
                    last_token_value = '+'

                position += plus_count
                col_num += plus_count
                token_found = True
                continue

            # Revisar secuencias de '--' y '-'
            if code[position] == '-':
                minus_count = 0
                temp_pos = position
                while temp_pos < code_len and code[temp_pos] == '-':
                    minus_count += 1
                    temp_pos += 1

                for i in range(minus_count // 2):
                    tokens.append(Token(TokenType.DECREMENT, '--', line_num, col_num + i * 2))
                    last_token_type = TokenType.DECREMENT
                    last_token_value = '--'

                if minus_count % 2 == 1:
                    tokens.append(Token(TokenType.ARITHMETIC_OP, '-', line_num, col_num + (minus_count - 1)))
                    last_token_type = TokenType.ARITHMETIC_OP
                    last_token_value = '-'

                position += minus_count
                col_num += minus_count
                token_found = True
                continue




            for pattern, token_type in self.patterns:
                match = pattern.match(code[position:])
                if match:
                    lexeme = match.group(0)
                    token_line = line_num
                    token_col = col_num

                    # Reclasificar NUMBER como INTEGER o DECIMAL
                    if token_type == TokenType.NUMBER:
                        if '.' in lexeme or 'e' in lexeme.lower():
                            token_type = TokenType.DECIMAL
                        else:
                            token_type = TokenType.INTEGER

                    # Actualizar líneas y columnas
                    newlines = lexeme.count('\n')
                    if newlines > 0:
                        line_num += newlines
                        col_num = len(lexeme.rsplit('\n', 1)[-1]) + 1
                    else:
                        col_num += len(lexeme)





                    # Verificaciones
                    if token_type == TokenType.IDENTIFIER and lexeme in self.reserved_words:
                        token_type = TokenType.RESERVED_WORD

                    if token_type == TokenType.NUMBER:
                        if lexeme.count('.') > 1 or lexeme.endswith('.'):
                            errors.append(f"Error léxico: Número mal formado '{lexeme}' en línea {token_line}, columna {token_col}.")
                            tokens.append(Token(TokenType.ERROR, lexeme, token_line, token_col))
                            last_token_type = TokenType.ERROR
                            last_token_value = lexeme
                            position += len(lexeme)
                            token_found = True
                            break

                   #if token_type in {TokenType.ARITHMETIC_OP, TokenType.RELATIONAL_OP, TokenType.LOGICAL_OP}:
                       # if lexeme in self.binary_operators and last_token_type not in [TokenType.NUMBER, TokenType.IDENTIFIER, TokenType.CHAR, TokenType.STRING] and last_token_value not in [')', ']']:
                        #    errors.append(f"Error léxico: Operador '{lexeme}' en línea {token_line}, columna {token_col} sin operando izquierdo válido.")

                    if lexeme in self.delimiter_pairs:
                        open_delimiters.append((lexeme, token_line, token_col))
                    elif lexeme in self.delimiter_pairs.values():
                        expected_opener = next((o for o, c in self.delimiter_pairs.items() if c == lexeme), None)
                        if not open_delimiters:
                            errors.append(f"Error léxico: Delimitador de cierre '{lexeme}' en línea {token_line}, columna {token_col} sin apertura.")
                        elif open_delimiters[-1][0] != expected_opener:
                            opener, o_line, o_col = open_delimiters[-1]
                            errors.append(f"Error léxico: Cierre '{lexeme}' en línea {token_line}, columna {token_col} no coincide con apertura '{opener}' en línea {o_line}, columna {o_col}.")
                        else:
                            open_delimiters.pop()

                    if token_type == TokenType.ASSIGNMENT:
                        if last_token_type not in [TokenType.IDENTIFIER, TokenType.ASSIGNMENT]:
                            errors.append(f"Error léxico: Asignación inválida en línea {token_line}, columna {token_col}.")

                    if token_type == TokenType.LOGICAL_OP and lexeme in ['&&', '||']:
                        lookahead = code[position + len(lexeme):]
                        next_match = re.match(r'\s*[\)\]\};]?', lookahead)
                        if next_match and next_match.group(0).strip() in [')', ']', '}', ';', '']:
                            errors.append(f"Error léxico: Operador lógico '{lexeme}' en línea {token_line}, columna {token_col} con expresión incompleta.")


                    token = Token(token_type, lexeme, token_line, token_col)
                    tokens.append(token)
                    if token_type == TokenType.ERROR:
                        errors.append(f"Error léxico: Lexema no válido '{lexeme}' en línea {token_line}, columna {token_col}.")
                        
                    last_token_type = token_type
                    last_token_value = lexeme
                    position += len(lexeme)
                    token_found = True
                    break

            if not token_found:
                char = code[position]
                errors.append(f"Error léxico: Carácter no reconocido '{char}' en línea {line_num}, columna {col_num}.")
                tokens.append(Token(TokenType.ERROR, char, line_num, col_num))
                if char == '\n':
                    line_num += 1
                    col_num = 1
                else:
                    col_num += 1
                position += 1

        for opener, lnum, col in open_delimiters:
            closer = self.delimiter_pairs[opener]
            errors.append(f"Error léxico: Delimitador de apertura '{opener}' en línea {lnum}, columna {col} sin cierre '{closer}'.")

        self.check_control_structures(code, errors)

        return tokens, errors

    ##############################################################
    
    def get_error_suggestion(self, error_char, last_token_type, last_token_value, line, position):
        """Proporciona sugerencias contextuales para errores léxicos"""
        
        # Verificar si es un carácter especial que podría ser parte de un operador
        if error_char in '@#$%^&*':
            return f"Los caracteres especiales no son válidos en este lenguaje. Si intentaba usar un operador, los operadores válidos son: +, -, *, /, %, ^, ++, --, ==, !=, <, >, <=, >=, &&, ||, !"
        
        # Verificar si es un número seguido de una letra (posible identificador mal formado)
        if error_char.isalpha() and last_token_type == TokenType.NUMBER:
            return f"Los identificadores deben comenzar con una letra. Un número no puede ser seguido directamente por una letra."
        
        # Verificar si es un posible operador incompleto
        if error_char in '&|':
            next_pos = position + 1
            if next_pos < len(line) and line[next_pos] != error_char:
                return f"Operador incompleto. Si intentaba usar un operador lógico, use '&&' para AND o '||' para OR."
        
        # Verificar si es un posible delimitador incorrecto
        if error_char in ')}]':
            for opener, closer in self.delimiter_pairs.items():
                if closer == error_char:
                    return f"Delimitador de cierre sin su correspondiente delimitador de apertura '{opener}'."
        
        # Sugerencia genérica
        return "Verifique la sintaxis del lenguaje para caracteres y operadores válidos."
    
    def check_control_structures(self, code, errors):
        """Verifica estructuras de control incompletas o mal formadas"""
        
        # Verificar estructuras if-then-else-end
        if_blocks = re.finditer(r'if\s*$$[^)]*$$', code)
        for match in if_blocks:
            if_pos = match.start()
            line_num = code[:if_pos].count('\n') + 1
            column = if_pos - code[:if_pos].rfind('\n') if '\n' in code[:if_pos] else if_pos + 1
            
            # Verificar si hay un 'then' después del if
            then_match = re.search(r'\bthen\b', code[match.end():])
            if not then_match:
                errors.append(f"Error estructural: 'if' en línea {line_num}, columna {column} sin 'then' correspondiente.")
            
            # Verificar si hay un 'end' para cerrar el bloque if
            end_match = re.search(r'\bend\b', code[match.end():])
            if not end_match:
                errors.append(f"Error estructural: 'if' en línea {line_num}, columna {column} sin 'end' correspondiente.")
        
        # Verificar estructuras do-until
        do_blocks = re.finditer(r'\bdo\b', code)
        for match in do_blocks:
            do_pos = match.start()
            line_num = code[:do_pos].count('\n') + 1
            column = do_pos - code[:do_pos].rfind('\n') if '\n' in code[:do_pos] else do_pos + 1
            
            # Verificar si hay un 'until' después del do
            until_match = re.search(r'\buntil\s*$$[^)]*$$', code[match.end():])
            if not until_match:
                errors.append(f"Error estructural: 'do' en línea {line_num}, columna {column} sin 'until' correspondiente o con formato incorrecto.")
        
        # Verificar condiciones incompletas en estructuras de control
        condition_patterns = [
            (r'if\s*$$[^)]*&&\s*$$', 'if'),
            (r'if\s*$$[^)]*\|\|\s*$$', 'if'),
            (r'while\s*$$[^)]*&&\s*$$', 'while'),
            (r'while\s*$$[^)]*\|\|\s*$$', 'while'),
            (r'until\s*$$[^)]*&&\s*$$', 'until'),
            (r'until\s*$$[^)]*\|\|\s*$$', 'until')
        ]
        
        for pattern, structure in condition_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                pos = match.start()
                line_num = code[:pos].count('\n') + 1
                column = pos - code[:pos].rfind('\n') if '\n' in code[:pos] else pos + 1
                errors.append(f"Error estructural: Condición incompleta en '{structure}' en línea {line_num}, columna {column}. Operador lógico sin operando derecho.")
        
        # Verificar asignaciones incompletas o mal formadas
        assignment_patterns = [
            (r'[a-zA-Z][a-zA-Z0-9]*\s*=\s*;', 'asignación sin valor'),
            (r'[a-zA-Z][a-zA-Z0-9]*\s*=\s*=', 'múltiples signos de igualdad'),
            #(r'=\s*[a-zA-Z0-9]', 'asignación sin identificador a la izquierda')
        ]
        
        for pattern, error_type in assignment_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                pos = match.start()
                line_num = code[:pos].count('\n') + 1
                column = pos - code[:pos].rfind('\n') if '\n' in code[:pos] else pos + 1
                errors.append(f"Error estructural: {error_type.capitalize()} en línea {line_num}, columna {column}.")
