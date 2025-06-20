import os
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, Menu
import re

# Importamos las clases para el analizador léxico
from lexico import TokenType, Token, LexicalAnalyzer

from sintactico import Parser
from arbol_sintaxis import ASTNode



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
            TokenType.STRING: "#93b121",         # Verde oscuro
            TokenType.INCREMENT: "#0080FF",    # Azul brillante
            TokenType.DECREMENT: "#FF8000",   # Naranja fuerte
            TokenType.INTEGER: "#007ACC",   # Azul para enteros
            TokenType.DECIMAL: "#009688"   # Otro color para decimales (o el mismo si prefieres)

        }
                # Aplicar estilo moderno a la interfaz
        self.estilo = ttk.Style()
        self.estilo.theme_use('clam')  # O usa 'alt', 'default', 'vista', según lo que tengas instalado

        # Personalizar colores y widgets
        self.estilo.configure('.', font=('Segoe UI', 10))
        self.estilo.configure('TButton', padding=6, relief='flat', background='#4A90E2', foreground='white')
        self.estilo.map('TButton', background=[('active', '#357ABD')])
        self.estilo.configure('TNotebook.Tab', padding=[10, 5], font=('Segoe UI', 9, 'bold'))

        # Fondo más claro para editor y pestañas
        self.estilo.configure('TFrame', background='#f0f0f0')
        self.estilo.configure('TNotebook', background='#e6e6e6')
        self.estilo.configure('TLabel', background='#f0f0f0')

        # Colores específicos para estado
        self.estilo.configure('Status.TLabel', background='#e6e6e6', foreground='#333333', font=('Segoe UI', 9))

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
        self.status_position = ttk.Label(status_frame, text="Línea: 1, Columna: 1", style='Status.TLabel')
        self.line_count_label = ttk.Label(status_frame, text="Total líneas: 1", style='Status.TLabel')
        self.file_info = ttk.Label(status_frame, text="No guardado", style='Status.TLabel')

       
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

        self.tabSintactico = ttk.Treeview(self.pestanasAnalisis, columns=("Tipo", "Línea", "Columna"), show='tree headings')
        self.tabSintactico.heading("#0", text="Nodo")
        self.tabSintactico.heading("Tipo", text="Tipo")
        self.tabSintactico.heading("Línea", text="Línea")
        self.tabSintactico.heading("Columna", text="Columna")

        self.tabSintactico.column("#0", width=200)
        self.tabSintactico.column("Tipo", width=100, anchor="center")
        self.tabSintactico.column("Línea", width=60, anchor="center")
        self.tabSintactico.column("Columna", width=80, anchor="center")



        scroll_sintactico = ttk.Scrollbar(self.pestanasAnalisis, orient="vertical", command=self.tabSintactico.yview)
        self.tabSintactico.configure(yscrollcommand=scroll_sintactico.set)
        self.tabSintactico.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_sintactico.pack(side=tk.RIGHT, fill=tk.Y)

        self.tabLexico = scrolledtext.ScrolledText(self.pestanasAnalisis, wrap=tk.WORD)
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
        self.tabErrores.tag_configure("error", foreground="black", spacing3=0)
        self.tabErrores.tag_configure("warning", foreground="orange")
        self.tabErrores.tag_configure("info", foreground="blue")

    def on_key_press(self, event=None):
        self.actualizar_numeros_linea()
        return True
    
    def on_key_release(self, event=None):
        self.update_status_bar()
        self.highlight_syntax()
        return True
    
    def imprimir_arbol_tabla(self, nodo, nivel=0, filas=None):
        if filas is None:
            filas = []

        if nodo:
            nombre = nodo.name if hasattr(nodo, 'name') else 'n/a'
            tipo = nodo.node_type if hasattr(nodo, 'node_type') else 'n/a'
            linea = str(nodo.line) if hasattr(nodo, 'line') else "-"
            columna = str(nodo.column) if hasattr(nodo, 'column') else "-"
            filas.append(f"{nombre:<20}{tipo:<20}{linea:<10}{columna:<10}")
            for hijo in nodo.children:
                self.imprimir_arbol_tabla(hijo, nivel + 1, filas)
        return filas


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
        for tag in self.editor.tag_names():
            if tag != "sel":
                self.editor.tag_remove(tag, "1.0", tk.END)

        code = self.editor.get(1.0, tk.END)
        tokens, _ = self.analizador_lexico.analyze(code)

        for token in tokens:
            if not token.value.strip():
                continue

            try:
                start_line = token.line
                start_col = token.column - 1
                start_pos = f"{start_line}.{start_col}"

                lines = token.value.split('\n')
                if len(lines) == 1:
                    end_line = start_line
                    end_col = start_col + len(token.value)
                else:
                    end_line = start_line + len(lines) - 1
                    end_col = len(lines[-1])

                end_pos = f"{end_line}.{end_col}"

                tag_name = f"tag_{token.type.name}"
                if tag_name not in self.editor.tag_names():
                    self.editor.tag_configure(tag_name, foreground=self.token_colors[token.type])

                self.editor.tag_add(tag_name, start_pos, end_pos)

            except Exception:
                continue  # Ignora errores de tokens mal posicionados



                
    def fase_compilacion(self, fase):
        if not self.archivo_guardar():
            return

        # Limpiar pestaña de errores
        self.tabErrores.delete('1.0', tk.END)

        # Obtener el código
        code = self.editor.get('1.0', 'end-1c')
        # === ANÁLISIS LÉXICO ===
        if fase == "lexico" or fase == "all":
            tokens, errors = self.analizador_lexico.analyze(code)

            self.tabLexico.delete('1.0', tk.END)
            self.tabLexico.insert('1.0', f"{'Tipo':<20}{'Valor':<20}{'Línea':<10}{'Columna':<10}\n")
            self.tabLexico.insert(tk.END, "-" * 60 + "\n")

            for token in tokens:
                if token.type not in [TokenType.ERROR, TokenType.COMMENT]:
                    self.tabLexico.insert(
                        tk.END,
                        f"{token.type.name:<20}{token.value:<20}{token.line:<10}{token.column:<10}\n"
                    )

            # Mostrar errores solo si se está en análisis léxico o 'all'
            if fase == "lexico" or fase == "all":
                self.tabErrores.delete('1.0', tk.END)  # Limpiar antes de mostrar errores nuevos
                if errors:
                    self.tabErrores.insert('1.0', "Errores detectados:\n\n", "error")
                    for i, error in enumerate(errors, 1):
                        self.tabErrores.insert(tk.END, f"{i}. {error}\n\n", "error")
                    self.pestanasErroresSalida.select(0)
                else:
                    self.tabErrores.insert('1.0', "No se encontraron errores en el análisis léxico.\n", "info")

            # === Tabla de Símbolos ===
            self.tabTablaSimbolos.delete('1.0', tk.END)
            self.tabTablaSimbolos.insert('1.0', "Tabla de Símbolos:\n\n")
            self.tabTablaSimbolos.insert(tk.END, f"{'Identificador':<20}{'Tipo':<15}{'Línea':<10}{'Columna':<10}\n")
            self.tabTablaSimbolos.insert(tk.END, "-" * 55 + "\n")

            unique_identifiers = {}
            for token in tokens:
                if token.type == TokenType.IDENTIFIER and token.value not in unique_identifiers:
                    unique_identifiers[token.value] = token

            for value, token in unique_identifiers.items():
                self.tabTablaSimbolos.insert(
                    tk.END, f"{token.value:<20}{'IDENTIFICADOR':<15}{token.line:<10}{token.column:<10}\n"
                )

            for token in tokens:
                if token.type == TokenType.RESERVED_WORD and token.value not in unique_identifiers:
                    self.tabTablaSimbolos.insert(
                        tk.END, f"{token.value:<20}{'RESERVADA':<15}{token.line:<10}{token.column:<10}\n"
                    )

            self.pestanasAnalisis.select(0)


        # === ANÁLISIS SINTÁCTICO ===
        if fase == "sintactico" or fase == "all":
            for item in self.tabSintactico.get_children():
                self.tabSintactico.delete(item)


            tokens, _ = self.analizador_lexico.analyze(code)  # Ignora errores léxicos aquí
            parser = Parser(tokens)
            ast, sintax_errors = parser.parse()
            # 🔍 DEBUG: Ver hijos de nodos INCREMENT/DECREMENT
            for nodo in ast.children:
                if nodo.node_type in ["INCREMENT", "DECREMENT"]:
                    print(f"[DEBUG] {nodo.name} tiene {len(nodo.children)} hijo(s)")
                    for hijo in nodo.children:
                        print("     ↳", hijo.name)


            #if any("Error léxico" in e for e in errors):
             #   messagebox.showwarning("Advertencia", "Existen errores léxicos. Se continúa con el análisis sintáctico.")

            if sintax_errors:
                pass
            else:
                messagebox.showinfo("Sintaxis", "Análisis sintáctico exitoso.")

            if ast:
                self.insertar_en_treeview(self.tabSintactico, ast)
                self.mostrar_ast_como_tabla(ast)


            


        # === ANÁLISIS SEMÁNTICO ===
        if fase == "semantico" or fase == "all":
            self.tabSemantico.delete('1.0', tk.END)
            self.tabSemantico.insert('1.0', "Análisis semántico no implementado todavía.\n")
            if fase == "semantico":
                self.pestanasAnalisis.select(2)

        # === CÓDIGO INTERMEDIO ===
        if fase == "intermedio" or fase == "all":
            self.tabIntermedio.delete('1.0', tk.END)
            self.tabIntermedio.insert('1.0', "Generación de código intermedio no implementada todavía.\n")
            if fase == "intermedio":
                self.pestanasAnalisis.select(3)



    def insertar_en_treeview(self, treeview, nodo, parent=""):
        if nodo is None or "ERROR" in getattr(nodo, 'name', ''):
            return

        nombre = getattr(nodo, 'name', 'n/a')
        tipo = getattr(nodo, 'node_type', '')
        linea = getattr(nodo, 'line', 0)
        columna = getattr(nodo, 'column', 0)

    #  Corregimos: quitar "NodeType." para que sea más limpio
        if hasattr(tipo, "name"):
         tipo_texto = tipo.name
        else:
         tipo_texto = str(tipo)

        if "(" in nombre and ")" in nombre:
         nodo_texto = nombre
        elif tipo_texto:
         nodo_texto = f"{tipo_texto} ({nombre})"
        else:
         nodo_texto = nombre

        item_id = treeview.insert(parent, tk.END, text=nodo_texto, values=(tipo_texto, linea, columna))

    # Abrir automáticamente el nodo insertado
        treeview.item(item_id, open=True)

    # Recursivamente insertar hijos
        for hijo in getattr(nodo, 'children', []):
            self.insertar_en_treeview(treeview, hijo, parent=item_id)






    def mostrar_ast_como_tabla(self, nodo):
       def recorrer(nodo, nivel=0, filas=None):
        if filas is None:
            filas = []
        if nodo:
            filas.append({
                "Nombre": nodo.name,
                "Tipo": nodo.node_type.name,
                "Línea": nodo.line,
                "Columna": nodo.column,
                "Nivel": nivel
            })
            for hijo in nodo.children:
                recorrer(hijo, nivel + 1, filas)
        return filas

       filas = recorrer(nodo)
       for fila in filas:
        print(f"{'  ' * fila['Nivel']}- {fila['Nombre']} [{fila['Tipo']}] (Línea {fila['Línea']}, Columna {fila['Columna']})") 


            
    def imprimir_arbol(self, nodo, nivel=0):
        resultado = ""
        if nodo:
            indentacion = "  " * nivel
            resultado += f"{indentacion}- {nodo.name}\n"
            for hijo in nodo.children:
                resultado += self.imprimir_arbol(hijo, nivel + 1)
        return resultado
    
    def generar_tabla_sintactica(self, nodo):
        filas = []

        def recorrer(n):
            if n:
                nombre = getattr(n, 'name', 'n/a')
                tipo = getattr(n, 'type', '')
                linea = getattr(n, 'line', '-')
                columna = getattr(n, 'column', '-')
                filas.append((nombre, tipo, linea, columna))
                for hijo in getattr(n, 'children', []):
                    recorrer(hijo)

        recorrer(nodo)
        return filas


    def ejecutar_codigo(self):
        self.tabSalida.delete('1.0', tk.END)
        self.tabSalida.insert('1.0', "La ejecución del código no está implementada todavía.\n")
        self.pestanasErroresSalida.select(1)
        
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