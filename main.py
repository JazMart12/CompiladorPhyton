import tkinter as tk
from compilador import CompiladorIDE

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("1200x800")
    app = CompiladorIDE(root)
    root.mainloop()