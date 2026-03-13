import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os


class GraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NoC Mapper")

        self.selecao = None
        self.roteamento = None
        self.dimensao = None
        self.matrix = []
        self.loaded_config = False

        self.C = {
            "bg":      "#F5F3EF",
            "surface": "#EDEAE4",
            "card":    "#FFFFFF",
            "border":  "#D6D1C8",
            "accent":  "#2C2C2C",
            "text":    "#1A1A1A",
            "muted":   "#888078",
            "ink":     "#3D3A35",
            "rule":    "#C8C3BA",
        }

        self.setup_ui()

    def setup_ui(self):
        C = self.C
        self.root.configure(bg=C["bg"])

        W, H = 440, 600
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self.root.resizable(True, True)
        self.root.minsize(380, 540)

        main = tk.Frame(self.root, bg=C["bg"])
        main.pack(fill="both", expand=True, padx=36, pady=30)
        main.columnconfigure(0, weight=1)

        # HEADER
        tk.Label(main, text="NoC Mapper", bg=C["bg"], fg=C["text"],
                 font=("Georgia", 22, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(main, text="Network-on-Chip Mapping Tool", bg=C["bg"], fg=C["muted"],
                 font=("Georgia", 9, "italic")).grid(row=1, column=0, sticky="w")
        tk.Frame(main, bg=C["rule"], height=1).grid(row=2, column=0, sticky="ew", pady=(12, 0))

        # LOAD
        self._btn(main, "↑  Carregar arquivo de configuração",
                  self.carregar_arquivo_config, style="outline").grid(
            row=3, column=0, sticky="ew", pady=(14, 0), ipady=8)
        tk.Frame(main, bg=C["rule"], height=1).grid(row=4, column=0, sticky="ew", pady=(14, 0))

        # MÉTRICAS
        tk.Label(main, text="Métricas", bg=C["bg"], fg=C["ink"],
                 font=("Georgia", 12, "bold")).grid(row=5, column=0, sticky="w", pady=(14, 4))

        self.variaveis_checkbox = []
        for i, label in enumerate(["Energia", "Latência", "Tolerância a falha"]):
            var = tk.IntVar()
            self.variaveis_checkbox.append(var)
            tk.Checkbutton(main, text=label, variable=var,
                           bg=C["bg"], fg=C["text"],
                           activebackground=C["bg"], activeforeground=C["text"],
                           selectcolor=C["bg"],
                           font=("Georgia", 10),
                           relief="flat", bd=0, cursor="hand2",
                           highlightthickness=0).grid(row=6+i, column=0, sticky="w", padx=2, pady=1)

        tk.Frame(main, bg=C["rule"], height=1).grid(row=9, column=0, sticky="ew", pady=(14, 0))

        # GRID SIZE
        tk.Label(main, text="Grid (n × n)", bg=C["bg"], fg=C["ink"],
                 font=("Georgia", 12, "bold")).grid(row=10, column=0, sticky="w", pady=(14, 6))

        ef = tk.Frame(main, bg=C["border"])
        ef.grid(row=11, column=0, sticky="ew")
        ef.columnconfigure(0, weight=1)
        self.entrada_novo_valor = tk.Entry(ef, bg=C["card"], fg=C["text"],
                                           insertbackground=C["accent"],
                                           relief="flat", bd=0,
                                           font=("Georgia", 11),
                                           highlightthickness=1,
                                           highlightbackground=C["border"],
                                           highlightcolor=C["accent"])
        self.entrada_novo_valor.pack(fill="x", padx=1, pady=1, ipady=7, ipadx=10)

        tk.Frame(main, bg=C["rule"], height=1).grid(row=12, column=0, sticky="ew", pady=(14, 0))

        # ROTEAMENTO
        tk.Label(main, text="Roteamento", bg=C["bg"], fg=C["ink"],
                 font=("Georgia", 12, "bold")).grid(row=13, column=0, sticky="w", pady=(14, 6))

        style = ttk.Style()
        try: style.theme_use("clam")
        except: pass
        style.configure("Clean.TCombobox",
                        fieldbackground=C["card"], background=C["card"],
                        foreground=C["text"], arrowcolor=C["ink"],
                        relief="flat", padding=7, font=("Georgia", 10))
        style.map("Clean.TCombobox",
                  fieldbackground=[("readonly", C["card"])],
                  foreground=[("readonly", C["text"])])

        self.valor_selecionado = tk.StringVar(value="XY")
        combo_frame = tk.Frame(main, bg=C["border"])
        combo_frame.grid(row=14, column=0, sticky="ew")
        self.combo = ttk.Combobox(combo_frame, values=["XY", "XYX", "Negative First"],
                                  textvariable=self.valor_selecionado,
                                  state="readonly", style="Clean.TCombobox",
                                  font=("Georgia", 10))
        self.combo.pack(fill="x", padx=1, pady=1)

        tk.Frame(main, bg=C["rule"], height=1).grid(row=15, column=0, sticky="ew", pady=(20, 0))

        # CALCULAR
        self._btn(main, "Calcular", self.atualizar_valores, style="filled").grid(
            row=16, column=0, sticky="ew", pady=(16, 0), ipady=10)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _btn(self, parent, text, command, style="filled"):
        C = self.C
        if style == "filled":
            bg, fg, hbg = C["accent"], "#FFFFFF", C["ink"]
        else:
            bg, fg, hbg = C["bg"], C["ink"], C["surface"]

        wrapper = tk.Frame(parent, bg=C["border"])
        lbl = tk.Label(wrapper, text=text, bg=bg, fg=fg,
                       font=("Georgia", 10, "bold" if style == "filled" else "normal"),
                       cursor="hand2", relief="flat", bd=0)
        lbl.pack(fill="both", padx=1, pady=1)
        lbl.bind("<Button-1>", lambda e: command())
        lbl.bind("<Enter>",  lambda e: lbl.configure(bg=hbg))
        lbl.bind("<Leave>",  lambda e: lbl.configure(bg=bg))
        return wrapper

    def _themed_window(self, title, w, h):
        C = self.C
        win = tk.Tk()
        win.title(title)
        win.configure(bg=C["bg"])
        win.resizable(False, False)
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        return win

    def _entry_frame(self, parent):
        C = self.C
        f = tk.Frame(parent, bg=C["border"])
        e = tk.Entry(f, bg=C["card"], fg=C["text"],
                     insertbackground=C["accent"],
                     relief="flat", bd=0, font=("Georgia", 11),
                     highlightthickness=0)
        e.pack(fill="x", padx=1, pady=1, ipady=7, ipadx=10)
        return f, e

    # ── logic ─────────────────────────────────────────────────────────────────

    def carregar_arquivo_config(self):
        arquivo = filedialog.askopenfilename(
            title="Selecionar configuração",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
            initialdir=os.path.expanduser("~")
        )
        if not arquivo:
            return
        try:
            with open(arquivo) as f:
                dados = json.load(f)

            if "matriz_adj" not in dados or "grid_size" not in dados:
                messagebox.showerror("Erro", "Arquivo inválido: campos obrigatórios ausentes.")
                return

            matrix = dados["matriz_adj"]
            grid   = dados["grid_size"]

            if not isinstance(matrix, list) or len(matrix) == 0:
                messagebox.showerror("Erro", "matriz_adj inválida."); return
            n = len(matrix)
            for row in matrix:
                if len(row) != n:
                    messagebox.showerror("Erro", "Matriz não é quadrada."); return
                for v in row:
                    if not isinstance(v, (int, float)):
                        messagebox.showerror("Erro", "Elementos devem ser números."); return

            self.matrix   = matrix
            self.dimensao = (int(grid), int(grid)) if not isinstance(grid, list) else tuple(grid)
            self.size     = n

            if n > self.dimensao[0] * self.dimensao[1]:
                messagebox.showerror("Erro", "Tarefas excedem a grid."); return

            if isinstance(dados.get("metricas"), list):
                for i, v in enumerate(dados["metricas"]):
                    if i < len(self.variaveis_checkbox):
                        self.variaveis_checkbox[i].set(v)
                self.selecao = dados["metricas"].copy()
            else:
                self.selecao = [0] * 3

            if "roteamento" in dados:
                self.roteamento = dados["roteamento"]
                self.valor_selecionado.set(self.roteamento)

            self.entrada_novo_valor.delete(0, tk.END)
            self.entrada_novo_valor.insert(0, str(self.dimensao[0]))

            messagebox.showinfo("Sucesso", "Configuração carregada.")
            self.loaded_config = True
            self.root.destroy()
            self.create_graph()

        except json.JSONDecodeError:
            messagebox.showerror("Erro", "JSON inválido.")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def salvar_config_arquivo(self, _):
        arquivo = filedialog.asksaveasfilename(
            title="Salvar configuração",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialdir=os.path.expanduser("~"),
            initialfile="configuracao.json"
        )
        if not arquivo:
            return
        try:
            with open(arquivo, 'w') as f:
                json.dump({"matriz_adj": self.matrix, "grid_size": self.dimensao[0],
                           "metricas": self.selecao, "roteamento": self.roteamento}, f, indent=4)
            messagebox.showinfo("Sucesso", f"Salvo em:\n{arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def atualizar_valores(self):
        self.selecao    = [v.get() for v in self.variaveis_checkbox]
        self.roteamento = self.combo.get()
        dim = self.entrada_novo_valor.get().strip()
        try:
            self.dimensao = (int(dim), int(dim))
            self.root.destroy()
            self.get_matrix_size()
        except ValueError:
            messagebox.showerror("Erro", "Insira um valor numérico para a dimensão.")

    def get_matrix_size(self):
        C = self.C
        win = self._themed_window("Dimensão da Matriz", 340, 160)
        pad = tk.Frame(win, bg=C["bg"])
        pad.pack(fill="both", expand=True, padx=30, pady=24)

        tk.Label(pad, text="Tamanho da matriz de adjacência", bg=C["bg"], fg=C["ink"],
                 font=("Georgia", 11, "bold")).pack(anchor="w")
        tk.Label(pad, text="Número de tarefas", bg=C["bg"], fg=C["muted"],
                 font=("Georgia", 9)).pack(anchor="w", pady=(2, 10))

        ef, self.entry = self._entry_frame(pad)
        ef.pack(fill="x")
        tk.Frame(pad, bg=C["bg"], height=10).pack()
        self._btn(pad, "Confirmar", self.get_matrix_entries, "filled").pack(fill="x", ipady=8)
        self.matrix_window = win

    def get_matrix_entries(self):
        C = self.C
        try:
            self.size = int(self.entry.get())
            if self.size <= 0:
                raise ValueError
            self.matrix_window.destroy()

            cell_px = min(54, max(36, 400 // self.size))
            W = self.size * (cell_px + 8) + 80
            H = self.size * (cell_px + 8) + 120

            win = self._themed_window("Matriz de Adjacência", W, H)
            self.matrix_input_window = win

            pad = tk.Frame(win, bg=C["bg"])
            pad.pack(fill="both", expand=True, padx=20, pady=20)

            tk.Label(pad, text=f"Matriz {self.size}×{self.size}", bg=C["bg"], fg=C["ink"],
                     font=("Georgia", 12, "bold")).pack(anchor="w", pady=(0, 10))

            grid_f = tk.Frame(pad, bg=C["bg"])
            grid_f.pack()

            self.matrix = []
            self.matrix_entry_widgets = []
            for i in range(self.size):
                row_entries = []
                for j in range(self.size):
                    ef = tk.Frame(grid_f, bg=C["border"])
                    ef.grid(row=i, column=j, padx=3, pady=3)
                    e = tk.Entry(ef, width=3, bg=C["card"], fg=C["text"],
                                 insertbackground=C["accent"],
                                 relief="flat", bd=0,
                                 font=("Georgia", 11), justify="center",
                                 highlightthickness=0)
                    e.pack(padx=1, pady=1, ipady=5, ipadx=4)
                    row_entries.append(e)
                self.matrix_entry_widgets.append(row_entries)

            tk.Frame(pad, bg=C["rule"], height=1).pack(fill="x", pady=(12, 0))
            self._btn(pad, "Confirmar matriz", self.submit_matrix, "filled").pack(
                fill="x", pady=(10, 0), ipady=8)

        except ValueError:
            messagebox.showerror("Erro", "Insira um inteiro positivo.")

    def submit_matrix(self):
        try:
            self.matrix = [[int(e.get()) for e in row] for row in self.matrix_entry_widgets]
            self.size = len(self.matrix)
            if self.size > self.dimensao[0] * self.dimensao[1]:
                messagebox.showerror("Erro", "Tarefas excedem a grid."); return
            self.matrix_input_window.destroy()
            self.create_graph()
        except ValueError:
            messagebox.showerror("Erro", "Valores inválidos.")

    def create_graph(self):
        import networkx as nx
        import matplotlib.pyplot as plt
        import matplotlib as mpl
        mpl.rcParams.update({"font.family": "serif"})

        G = nx.Graph()
        for i in range(self.size):
            for j in range(self.size):
                if self.matrix[i][j] != 0:
                    G.add_edge(i, j, weight=self.matrix[i][j])

        fig, ax = plt.subplots(figsize=(6, 5), facecolor="#F5F3EF")
        ax.set_facecolor("#F5F3EF")
        pos = nx.spring_layout(G, seed=42)
        edge_labels = nx.get_edge_attributes(G, 'weight')

        nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#C8C3BA", width=1.5)
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color="#2C2C2C", node_size=520)
        nx.draw_networkx_labels(G, pos, ax=ax, font_color="#F5F3EF",
                                font_size=9, font_family="serif")
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax,
                                      font_color="#888078", font_size=8, font_family="serif")
        ax.axis("off")
        fig.tight_layout()
        plt.savefig("grafo.png", dpi=150, facecolor=fig.get_facecolor())
        plt.show()
        self.verificação_da_corretude()

    def verificação_da_corretude(self):
        if messagebox.askyesno("Confirmação", "O grafo está correto?"):
            if not self.loaded_config:
                if messagebox.askyesno("Salvar", "Deseja salvar a configuração?"):
                    self.salvar_config_arquivo(None)
            self.mapeamentos()
        else:
            self.perguntar_novamente_matrix()

    def perguntar_novamente_matrix(self):
        C = self.C
        cell_px = min(54, max(36, 400 // self.size))
        W = self.size * (cell_px + 8) + 80
        H = self.size * (cell_px + 8) + 120
        win = self._themed_window("Matriz de Adjacência", W, H)
        self.matrix_input_window = win
        pad = tk.Frame(win, bg=C["bg"])
        pad.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(pad, text=f"Matriz {self.size}×{self.size}", bg=C["bg"], fg=C["ink"],
                 font=("Georgia", 12, "bold")).pack(anchor="w", pady=(0, 10))
        grid_f = tk.Frame(pad, bg=C["bg"])
        grid_f.pack()
        self.matrix = []
        self.matrix_entry_widgets = []
        for i in range(self.size):
            row_entries = []
            for j in range(self.size):
                ef = tk.Frame(grid_f, bg=C["border"])
                ef.grid(row=i, column=j, padx=3, pady=3)
                e = tk.Entry(ef, width=3, bg=C["card"], fg=C["text"],
                             insertbackground=C["accent"], relief="flat", bd=0,
                             font=("Georgia", 11), justify="center", highlightthickness=0)
                e.pack(padx=1, pady=1, ipady=5, ipadx=4)
                row_entries.append(e)
            self.matrix_entry_widgets.append(row_entries)
        tk.Frame(pad, bg=C["rule"], height=1).pack(fill="x", pady=(12, 0))
        self._btn(pad, "Confirmar matriz", self.submit_matrix, "filled").pack(
            fill="x", pady=(10, 0), ipady=8)

    def mapeamentos(self):
        print("mapeamentos() — integre seus algoritmos aqui.")

    def calcular_energia(self, mapeamento):
        if mapeamento is None:
            raise ValueError
        n, m, total = len(self.matrix), len(mapeamento), 0
        for i in range(n):
            for j in range(n):
                bw = self.matrix[i][j]
                if bw > 0:
                    ix, iy = [(r, c) for r in range(m) for c in range(m) if mapeamento[r][c] == i][0]
                    jx, jy = [(r, c) for r in range(m) for c in range(m) if mapeamento[r][c] == j][0]
                    total += bw * (abs(ix-jx) + abs(iy-jy))
        return total

    def calcular_tolerancia_falha(self, matriz):
        if matriz is None:
            raise ValueError
        dirs, tol = [(-1,0),(1,0),(0,-1),(0,1)], 0
        for i in range(len(matriz)):
            for j in range(len(matriz[i])):
                if matriz[i][j] != 0:
                    for dx, dy in dirs:
                        x, y = i+dx, j+dy
                        if 0 <= x < len(matriz) and 0 <= y < len(matriz[0]):
                            if matriz[x][y] != 0:
                                tol += 1
        return tol


if __name__ == "__main__":
    root = tk.Tk()
    app = GraphApp(root)
    root.mainloop()