import os
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, Menu
from enum import Enum

# Importamos las clases del analizador léxico
class TokenType(Enum):
    NUMBER = 1          # Enteros y reales (con/sin signo)
    IDENTIFIER = 2      # Identificadores
    COMMENT = 3         # Comentarios
    RESERVED_WORD = 4   # Palabras reservadas
    ARITHMETIC_OP = 5   # Operadores aritméticos
    RELATIONAL_OP = 6   # Operadores relacionales
    LOGICAL_OP = 6      # Operadores lógicos (mismo color que relacionales)
    SYMBOL = 7          # Símbolos
    ASSIGNMENT = 8      # Asignación
    ERROR = 9           # Error léxico
    CHAR = 10           # Caracteres 
    STRING = 11         # Cadenas 


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
            # Números enteros y reales
            (r'[+-]?\d+(\.\d+)?([eE][+-]?\d+)?', TokenType.NUMBER),
            
            # Comentarios de múltiples líneas
            (r'/\*[\s\S]*?\*/', TokenType.COMMENT),
            
            # Comentarios de una línea
            (r'//.*', TokenType.COMMENT),
            
            # Operadores aritméticos
            (r'[+\-*/\^%]|[+]{2}|[-]{2}', TokenType.ARITHMETIC_OP),
            
            # Operadores relacionales
            (r'<=|>=|==|!=|<|>', TokenType.RELATIONAL_OP),
            
            # Operadores lógicos
            (r'&&|\|\||!', TokenType.LOGICAL_OP),
            
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
    
    def analyze(self, code):
        tokens = []
        errors = []
        lines = code.split('\n')
        
        # Variables para seguimiento de estado
        open_delimiters = []  # Pila para seguimiento de delimitadores
        last_token_type = None
        last_token_value = None
        
        for line_num, line in enumerate(lines, 1):
            position = 0
            while position < len(line):
                # Ignorar espacios en blanco
                match = re.match(r'\s+', line[position:])
                if match:
                    position += match.end()
                    continue
                
                token_found = False
                
                for pattern, token_type in self.patterns:
                    match = pattern.match(line[position:])
                    if match:
                        lexeme = match.group(0)
                        column = position + 1
                        
                        # Verificar si es una palabra reservada
                        if token_type == TokenType.IDENTIFIER and lexeme in self.reserved_words:
                            token_type = TokenType.RESERVED_WORD
                        
                        # Verificar números mal formados (múltiples puntos decimales)
                        if token_type == TokenType.NUMBER and lexeme.count('.') > 1:
                            errors.append(f"Error léxico: Número mal formado '{lexeme}' en línea {line_num}, columna {column}. Un número solo puede tener un punto decimal.")
                            token_type = TokenType.ERROR
                        
                        # Verificar operadores binarios sin operandos adecuados
                        if token_type == TokenType.ARITHMETIC_OP or token_type == TokenType.RELATIONAL_OP or token_type == TokenType.LOGICAL_OP:
                            if lexeme in self.binary_operators:
                                # Verificar operando izquierdo
                                if last_token_type not in [TokenType.NUMBER, TokenType.IDENTIFIER, TokenType.CHAR, TokenType.STRING] and last_token_value not in [')', ']']:
                                    errors.append(f"Error léxico: Operador '{lexeme}' en línea {line_num}, columna {column} sin operando izquierdo válido. Se esperaba un número, identificador o expresión.")
                                
                                # Verificar operando derecho (mirando adelante)
                                next_pos = position + len(lexeme)
                                next_token_found = False
                                
                                # Saltar espacios en blanco
                                while next_pos < len(line) and line[next_pos].isspace():
                                    next_pos += 1
                                
                                # Si llegamos al final de la línea o encontramos un delimitador incorrecto
                                if next_pos >= len(line) or line[next_pos] in [';', ')', ']', '}']:
                                    errors.append(f"Error léxico: Operador '{lexeme}' en línea {line_num}, columna {column} sin operando derecho. Se esperaba un número, identificador o expresión.")
                        
                        # Verificar delimitadores
                        if lexeme in self.delimiter_pairs:
                            open_delimiters.append((lexeme, line_num, column))
                        elif lexeme in self.delimiter_pairs.values():
                            # Buscar el delimitador de apertura correspondiente
                            expected_opener = None
                            for opener, closer in self.delimiter_pairs.items():
                                if closer == lexeme:
                                    expected_opener = opener
                                    break
                            
                            if not open_delimiters:
                                errors.append(f"Error léxico: Delimitador de cierre '{lexeme}' en línea {line_num}, columna {column} sin delimitador de apertura correspondiente.")
                            elif open_delimiters[-1][0] != expected_opener:
                                opener, opener_line, opener_col = open_delimiters[-1]
                                errors.append(f"Error léxico: Delimitador de cierre '{lexeme}' en línea {line_num}, columna {column} no coincide con el delimitador de apertura '{opener}' en línea {opener_line}, columna {opener_col}.")
                            else:
                                open_delimiters.pop()
                        
                        # Verificar asignaciones incorrectas (múltiples signos =)
                        if token_type == TokenType.ASSIGNMENT:
                            # Mirar adelante para detectar múltiples signos =
                            next_pos = position + 1
                            while next_pos < len(line) and line[next_pos].isspace():
                                next_pos += 1
                            
                            if next_pos < len(line) and line[next_pos] == '=':
                                # Es un operador de igualdad (==), no un error
                                pass
                            else:
                                # Verificar si el token anterior es un identificador (asignación válida)
                                if last_token_type != TokenType.IDENTIFIER and last_token_type != TokenType.ASSIGNMENT:
                                    errors.append(f"Error léxico: Asignación inválida en línea {line_num}, columna {column}. Se esperaba un identificador antes del operador '='.")
                        
                        # Verificar operadores lógicos incompletos
                        if token_type == TokenType.LOGICAL_OP and lexeme in ['&&', '||']:
                            # Mirar adelante para detectar expresiones incompletas
                            next_pos = position + len(lexeme)
                            while next_pos < len(line) and line[next_pos].isspace():
                                next_pos += 1
                            
                            if next_pos >= len(line) or line[next_pos] in [')', ']', '}', ';']:
                                errors.append(f"Error léxico: Operador lógico '{lexeme}' en línea {line_num}, columna {column} con expresión incompleta. Se esperaba una expresión después del operador.")
                        
                        token = Token(token_type, lexeme, line_num, column)
                        tokens.append(token)
                        
                        # Actualizar el último token para verificaciones futuras
                        last_token_type = token_type
                        last_token_value = lexeme
                        
                        position += len(lexeme)
                        token_found = True
                        break
                
                if not token_found:
                    # Error léxico: carácter no reconocido
                    error_char = line[position]
                    
                    # Proporcionar sugerencias basadas en el contexto
                    suggestion = self.get_error_suggestion(error_char, last_token_type, last_token_value, line, position)
                    
                    errors.append(f"Error léxico: Carácter no reconocido '{error_char}' en línea {line_num}, columna {position+1}. {suggestion}")
                    
                    # Crear un token de error para resaltado
                    error_token = Token(TokenType.ERROR, error_char, line_num, position+1)
                    tokens.append(error_token)
                    
                    position += 1
        
        # Verificar delimitadores no cerrados al final del análisis
        for opener, line_num, column in open_delimiters:
            closer = self.delimiter_pairs[opener]
            errors.append(f"Error léxico: Delimitador de apertura '{opener}' en línea {line_num}, columna {column} sin delimitador de cierre '{closer}' correspondiente.")
        
        # Verificar estructuras de control incompletas
        self.check_control_structures(code, errors)
        
        return tokens, errors
    
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
            (r'=\s*[a-zA-Z0-9]', 'asignación sin identificador a la izquierda')
        ]
        
        for pattern, error_type in assignment_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                pos = match.start()
                line_num = code[:pos].count('\n') + 1
                column = pos - code[:pos].rfind('\n') if '\n' in code[:pos] else pos + 1
                errors.append(f"Error estructural: {error_type.capitalize()} en línea {line_num}, columna {column}.")


class CompiladorIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Compilador IDE")
        self.nombreArchivo = None
        
        # Inicializar el analizador léxico
        self.analizador_lexico = LexicalAnalyzer()
        
        # Definir colores para resaltado de sintaxis
        self.token_colors = {
            TokenType.NUMBER: "#007ACC",         # Azul
            TokenType.IDENTIFIER: "#000000",     # Negro
            TokenType.COMMENT: "#008000",        # Verde
            TokenType.RESERVED_WORD: "#800080",  # Púrpura
            TokenType.ARITHMETIC_OP: "#FF0000",  # Rojo
            TokenType.RELATIONAL_OP: "#FF8C00",  # Naranja
            TokenType.LOGICAL_OP: "#FF8C00",     # Naranja (Mismo que relacional)
            TokenType.SYMBOL: "#000000",         # Negro
            TokenType.ASSIGNMENT: "#FF0000",     # Rojo
            TokenType.ERROR: "#FF0000",          # Rojo
            TokenType.CHAR: "#93b121",           # Verde oscuro
            TokenType.STRING: "#93b121"          # Verde oscuro
        }
        
        self.configurar_interfaz()

    def configurar_interfaz(self):
        # Crear el menú principal
        self.barraMenu = tk.Menu(self.root)
        self.root.config(menu=self.barraMenu)

        # Menú Archivo
        menuArchivo = tk.Menu(self.barraMenu, tearoff=0)
        self.barraMenu.add_cascade(label="Archivo", menu=menuArchivo)
        menuArchivo.add_command(label="Nuevo", command=self.archivo_nuevo)
        menuArchivo.add_command(label="Abrir", command=self.archivo_abrir)
        menuArchivo.add_command(label="Guardar", command=self.archivo_guardar)
        menuArchivo.add_command(label="Guardar como", command=self.archivo_guardar_como)
        menuArchivo.add_separator()
        menuArchivo.add_command(label="Salir", command=self.root.quit)

        # Menú Compilador
        menuCompilador = tk.Menu(self.barraMenu, tearoff=0)
        self.barraMenu.add_cascade(label="Compilador", menu=menuCompilador)
        menuCompilador.add_command(label="Análisis Léxico", command=lambda: self.fase_compilacion("lexico"))
        menuCompilador.add_command(label="Análisis Sintáctico", command=lambda: self.fase_compilacion("sintactico"))
        menuCompilador.add_command(label="Análisis Semántico", command=lambda: self.fase_compilacion("semantico"))
        menuCompilador.add_command(label="Código Intermedio", command=lambda: self.fase_compilacion("intermedio"))
        menuCompilador.add_command(label="Ejecutar", command=self.ejecutar_codigo)

        # Menú Ayuda
        menuAyuda = tk.Menu(self.barraMenu, tearoff=0)
        self.barraMenu.add_cascade(label="Ayuda", menu=menuAyuda)
        menuAyuda.add_command(label="Acerca de", command=self.mostrar_acerca_de)

        # Barra de estado en la parte inferior
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_position = ttk.Label(status_frame, text="Línea: 1, Columna: 1")
        self.status_position.pack(side=tk.LEFT, padx=5)

        ttk.Separator(status_frame, orient='vertical').pack(side=tk.LEFT, fill='y', padx=5)

        self.line_count_label = ttk.Label(status_frame, text="Total líneas: 1")
        self.line_count_label.pack(side=tk.LEFT, padx=5)

        ttk.Separator(status_frame, orient='vertical').pack(side=tk.LEFT, fill='y', padx=5)

        self.file_info = ttk.Label(status_frame, text="No guardado")
        self.file_info.pack(side=tk.LEFT, padx=5)

        # Frame principal con tres paneles
        self.framePrincipal = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.framePrincipal.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Panel izquierdo (editor)
        self.frameIzquierdo = ttk.Frame(self.framePrincipal)
        self.framePrincipal.add(self.frameIzquierdo)

        # Panel derecho dividido (análisis arriba, errores/salida abajo)
        self.frameDerecho = ttk.PanedWindow(self.framePrincipal, orient=tk.VERTICAL)
        self.framePrincipal.add(self.frameDerecho)

        # Panel para análisis
        self.frameAnalisis = ttk.Frame(self.frameDerecho)
        self.frameDerecho.add(self.frameAnalisis)

        # Panel para errores y salida
        self.frameErroresSalida = ttk.Frame(self.frameDerecho)
        self.frameDerecho.add(self.frameErroresSalida)

        # Barra de herramientas
        barraHerramientas = ttk.Frame(self.frameIzquierdo)
        barraHerramientas.pack(fill=tk.X)

        # Crear botones sin iconos (podemos agregar iconos después)
        ttk.Button(barraHerramientas, text="Nuevo", command=self.archivo_nuevo).pack(side="left", padx=2)
        ttk.Button(barraHerramientas, text="Abrir", command=self.archivo_abrir).pack(side="left", padx=2)
        ttk.Button(barraHerramientas, text="Guardar", command=self.archivo_guardar).pack(side="left", padx=2)
        ttk.Button(barraHerramientas, text="Guardar como", command=self.archivo_guardar_como).pack(side="left", padx=2)
        ttk.Button(barraHerramientas, text="Compilar", command=lambda: self.fase_compilacion("all")).pack(side="left", padx=2)

        # Frame para el editor y números de línea
        frameEditor = ttk.Frame(self.frameIzquierdo)
        frameEditor.pack(fill=tk.BOTH, expand=True)

        # Editor de texto con números de línea
        self.numerosLinea = tk.Text(frameEditor, width=4, padx=3, takefocus=0, border=0,
                                  background='lightgray', state='disabled')
        self.numerosLinea.pack(side=tk.LEFT, fill=tk.Y)

        # Crear un frame contenedor para el editor y su scrollbar
        frameContenedorEditor = ttk.Frame(frameEditor)
        frameContenedorEditor.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Configurar el scrollbar del editor para sincronizar con los números de línea
        scrollbar = ttk.Scrollbar(frameContenedorEditor)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Editor con scrollbar
        self.editor = scrolledtext.ScrolledText(frameContenedorEditor, wrap=tk.WORD, undo=True, yscrollcommand=scrollbar.set)
        self.editor.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Conectar el scrollbar con el editor y números de línea
        scrollbar.config(command=self.on_scroll_both)
        
        # Configurar eventos para actualizar números de línea y resaltado de sintaxis
        self.editor.bind('<Key>', self.on_key_press)
        self.editor.bind('<KeyRelease>', self.on_key_release)
        self.editor.bind('<Button-1>', self.update_status_bar)
        self.editor.bind('<MouseWheel>', self.sincronizar_scroll)  # Para Windows
        self.editor.bind('<Button-4>', self.sincronizar_scroll)  # Para Linux (scroll up)
        self.editor.bind('<Button-5>', self.sincronizar_scroll)  # Para Linux (scroll down)

        # Panel de análisis (pestañas)
        self.pestanasAnalisis = ttk.Notebook(self.frameAnalisis)
        self.pestanasAnalisis.pack(fill=tk.BOTH, expand=True)

        # Pestañas para diferentes resultados de análisis
        self.tabLexico = scrolledtext.ScrolledText(self.pestanasAnalisis, wrap=tk.WORD)
        self.tabSintactico = scrolledtext.ScrolledText(self.pestanasAnalisis, wrap=tk.WORD)
        self.tabSemantico = scrolledtext.ScrolledText(self.pestanasAnalisis, wrap=tk.WORD)
        self.tabIntermedio = scrolledtext.ScrolledText(self.pestanasAnalisis, wrap=tk.WORD)
        self.tabTablaSimbolos = scrolledtext.ScrolledText(self.pestanasAnalisis, wrap=tk.WORD)

        self.pestanasAnalisis.add(self.tabLexico, text="Análisis Léxico")
        self.pestanasAnalisis.add(self.tabSintactico, text="Análisis Sintáctico")
        self.pestanasAnalisis.add(self.tabSemantico, text="Análisis Semántico")
        self.pestanasAnalisis.add(self.tabIntermedio, text="Código Intermedio")
        self.pestanasAnalisis.add(self.tabTablaSimbolos, text="Tabla de Símbolos")

        # Panel de errores y salida (pestañas)
        self.pestanasErroresSalida = ttk.Notebook(self.frameErroresSalida)
        self.pestanasErroresSalida.pack(fill=tk.BOTH, expand=True)

        # Pestañas para errores y salida
        self.tabErrores = scrolledtext.ScrolledText(self.pestanasErroresSalida, wrap=tk.WORD)
        self.tabSalida = scrolledtext.ScrolledText(self.pestanasErroresSalida, wrap=tk.WORD)

        self.pestanasErroresSalida.add(self.tabErrores, text="Errores")
        self.pestanasErroresSalida.add(self.tabSalida, text="Salida")

        # Configurar colores para errores
        self.tabErrores.tag_configure("error", foreground="red")
        self.tabErrores.tag_configure("warning", foreground="orange")
        self.tabErrores.tag_configure("info", foreground="blue")

    def on_key_press(self, event=None):
        self.actualizar_numeros_linea()
        return True
    
    def on_key_release(self, event=None):
        self.update_status_bar()
        self.highlight_syntax()
        return True

    def update_status_bar(self, event=None):
        # Actualizar información de posición del cursor
        cursor_position = self.editor.index(tk.INSERT)
        line, column = cursor_position.split('.')
        self.status_position.config(text=f"Línea: {line}, Columna: {int(column) + 1}")
    
        # Actualizar contador de líneas
        lines = self.editor.get('1.0', tk.END).count('\n')
        if lines < 1:
            lines = 1
        self.line_count_label.config(text=f"Total líneas: {lines}")
    
        # Actualizar información del archivo
        if self.nombreArchivo:
            self.file_info.config(text=f"{os.path.basename(self.nombreArchivo)}")
        else:
            self.file_info.config(text="No guardado")
    
        # También actualizamos números de línea
        self.actualizar_numeros_linea()
    
        return True

    def sincronizar_scroll(self, event=None):
        """Handle mouse wheel scrolling to synchronize editor and line numbers"""
        # For Windows and macOS
        if hasattr(event, 'delta'):
            if event.delta < 0:
                # Scroll down
                self.editor.yview_scroll(1, "units")
                self.numerosLinea.yview_scroll(1, "units")
            else:
                # Scroll up
                self.editor.yview_scroll(-1, "units")
                self.numerosLinea.yview_scroll(-1, "units")
        # For Linux
        else:
            if event.num == 4:
                # Scroll up
                self.editor.yview_scroll(-1, "units")
                self.numerosLinea.yview_scroll(-1, "units")
            elif event.num == 5:
                # Scroll down
                self.editor.yview_scroll(1, "units")
                self.numerosLinea.yview_scroll(1, "units")
        
        return "break"  # Prevent default behavior

    def actualizar_numeros_linea(self, event=None):
        # Obtener el número total de líneas
        contenido = self.editor.get('1.0', 'end-1c')
        lineas = contenido.count('\n') + 1
        
        # Generar texto con números de línea
        texto_numeros = '\n'.join(str(i) for i in range(1, lineas + 1))
        
        # Actualizar el widget de números de línea
        self.numerosLinea.config(state='normal')
        self.numerosLinea.delete('1.0', tk.END)
        self.numerosLinea.insert('1.0', texto_numeros)
        self.numerosLinea.config(state='disabled')
        
        # Sincronizar el scroll
        self.on_scroll('moveto', self.editor.yview()[0])
    
    def on_scroll(self, *args):
        # Sincronizar el scroll entre el editor y los números de línea
        if args[0] == 'moveto':
            self.numerosLinea.yview_moveto(args[1])
        elif args[0] == 'scroll':
            self.numerosLinea.yview_scroll(int(args[1]), args[2])
    
    def on_scroll_both(self, *args):
        # Sincroniza tanto el editor como los números de línea
        self.editor.yview(*args)
        self.numerosLinea.yview(*args)

    def archivo_nuevo(self):
        self.editor.delete('1.0', tk.END)
        self.nombreArchivo = None
        self.actualizar_numeros_linea()
        self.update_status_bar()

    def archivo_abrir(self):
        archivo = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if archivo:
            self.nombreArchivo = archivo
            self.editor.delete('1.0', tk.END)
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    self.editor.insert('1.0', f.read())
            except UnicodeDecodeError:
                # Intentar con otra codificación si utf-8 falla
                with open(archivo, 'r', encoding='latin-1') as f:
                    self.editor.insert('1.0', f.read())
            self.actualizar_numeros_linea()
            self.highlight_syntax()
            self.update_status_bar()
            self.root.title(f"Compilador IDE - {os.path.basename(archivo)}")

    def archivo_guardar(self):
        if not self.nombreArchivo:
            return self.archivo_guardar_como()

        try:
            content = self.editor.get('1.0', 'end-1c')
            with open(self.nombreArchivo, 'w', encoding='utf-8') as f:
                f.write(content)
            self.root.title(f"Compilador IDE - {os.path.basename(self.nombreArchivo)}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {str(e)}")
            return False 

    def archivo_guardar_como(self):
        archivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if archivo:
            self.nombreArchivo = archivo
            return self.archivo_guardar()
        return False

    def highlight_syntax(self):
        """Resaltar la sintaxis en el editor basado en el análisis léxico"""
        # Eliminar todos los tags actuales
        for tag in self.editor.tag_names():
            if tag != "sel":  # No eliminar la selección actual
                self.editor.tag_remove(tag, "1.0", tk.END)
        
        # Obtener el código actual
        code = self.editor.get(1.0, tk.END)
        
        # Analizar el código
        tokens, _ = self.analizador_lexico.analyze(code)
        
        # Aplicar colores según el tipo de token
        for token in tokens:
            start_pos = f"{token.line}.{token.column-1}"
            end_pos = f"{token.line}.{token.column-1 + len(token.value)}"
            
            tag_name = f"tag_{token.type.name}"
            if tag_name not in self.editor.tag_names():
                self.editor.tag_configure(tag_name, foreground=self.token_colors[token.type])
            
            self.editor.tag_add(tag_name, start_pos, end_pos)

    def fase_compilacion(self, fase):
        if not self.archivo_guardar():
            return
        
        # Limpiar pestaña de errores
        self.tabErrores.delete('1.0', tk.END)
        
        # Obtener el código
        code = self.editor.get('1.0', 'end-1c')
        
        if fase == "lexico" or fase == "all":
            # Realizar análisis léxico
            tokens, errors = self.analizador_lexico.analyze(code)
            
            # Mostrar los tokens en la pestaña correspondiente
            self.tabLexico.delete('1.0', tk.END)
            
            # Contar tokens por tipo
            token_counts = {}
            for token in tokens:
                if token.type.name in token_counts:
                    token_counts[token.type.name] += 1
                else:
                    token_counts[token.type.name] = 1
            
            # Mostrar resumen de tokens
            self.tabLexico.insert('1.0', "Análisis léxico completado\n\n")
            self.tabLexico.insert(tk.END, "Resumen de tokens:\n")
            for tipo, cantidad in token_counts.items():
                self.tabLexico.insert(tk.END, f"- {tipo}: {cantidad}\n")
            
            self.tabLexico.insert(tk.END, "\nListado de tokens:\n")
            for token in tokens:
                self.tabLexico.insert(tk.END, str(token) + '\n')
            
            # Mostrar errores si hay
            if errors:
                self.tabErrores.insert('1.0', "Errores detectados:\n\n", "error")
                for i, error in enumerate(errors, 1):
                    self.tabErrores.insert(tk.END, f"{i}. {error}\n\n", "error")
                self.pestanasErroresSalida.select(0)  # Seleccionar pestaña de errores
            else:
                self.tabErrores.insert('1.0', "No se encontraron errores en el análisis léxico.\n", "info")
            
            # Actualizar la tabla de símbolos
            self.tabTablaSimbolos.delete('1.0', tk.END)
            self.tabTablaSimbolos.insert('1.0', "Tabla de Símbolos:\n\n")
            self.tabTablaSimbolos.insert(tk.END, f"{'Identificador':<20}{'Tipo':<15}{'Línea':<10}{'Columna':<10}\n")
            self.tabTablaSimbolos.insert(tk.END, "-" * 55 + "\n")
            
            # Agregar solo identificadores a la tabla de símbolos (sin duplicados)
            unique_identifiers = {}
            for token in tokens:
                if token.type == TokenType.IDENTIFIER and token.value not in unique_identifiers:
                    unique_identifiers[token.value] = token
            
            for value, token in unique_identifiers.items():
                self.tabTablaSimbolos.insert(tk.END, f"{token.value:<20}{'IDENTIFICADOR':<15}{token.line:<10}{token.column:<10}\n")
                
            # También mostrar palabras reservadas en la tabla de símbolos
            for token in tokens:
                if token.type == TokenType.RESERVED_WORD and token.value not in unique_identifiers:
                    self.tabTablaSimbolos.insert(tk.END, f"{token.value:<20}{'RESERVADA':<15}{token.line:<10}{token.column:<10}\n")
            
            self.pestanasAnalisis.select(0)  # Seleccionar pestaña léxico
                    
        if fase == "sintactico" or fase == "all":
            self.tabSintactico.delete('1.0', tk.END)
            self.tabSintactico.insert('1.0', "Análisis sintáctico no implementado todavía.\n")
            if fase == "sintactico":
                self.pestanasAnalisis.select(1)  # Seleccionar pestaña sintáctico
        
        if fase == "semantico" or fase == "all":
            self.tabSemantico.delete('1.0', tk.END)
            self.tabSemantico.insert('1.0', "Análisis semántico no implementado todavía.\n")
            if fase == "semantico":
                self.pestanasAnalisis.select(2)  # Seleccionar pestaña semántico
        
        if fase == "intermedio" or fase == "all":
            self.tabIntermedio.delete('1.0', tk.END)
            self.tabIntermedio.insert('1.0', "Generación de código intermedio no implementada todavía.\n")
            if fase == "intermedio":
                self.pestanasAnalisis.select(3)  # Seleccionar pestaña intermedio

    def ejecutar_codigo(self):
        # Simulación de ejecución del código
        self.tabSalida.delete('1.0', tk.END)
        self.tabSalida.insert('1.0', "La ejecución del código no está implementada todavía.\n")
        self.pestanasErroresSalida.select(1)  # Seleccionar pestaña de salida
        
    def mostrar_acerca_de(self):
        messagebox.showinfo(
            "Acerca de",
            "Compilador IDE con Analizador Léxico Integrado\n"
            "Desarrollado para el curso de Compiladores I\n"
            "Mayo 2025"
        )


if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("1200x800")
    app = CompiladorIDE(root)
    root.mainloop()
