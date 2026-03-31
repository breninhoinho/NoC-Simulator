import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from Algoritmos_Mapeamento.Random import *
from Algoritmos_Mapeamento.Genetic_Algorithm import *
from Algoritmos_Mapeamento.Andean_condor import *
from Algoritmos_Mapeamento.Random import *
from Algoritmos_Mapeamento.Engineered_Mapping import *
from Algoritmos_Mapeamento.SimulatedAnneling import *
from Algoritmos_Mapeamento.Cluster_Based import *
from Algoritmos_Mapeamento.PSO import *
from Algoritmos_Mapeamento.NSGA2 import *
from Noc import *
import json
from time import sleep
import concurrent.futures
import time
import os



class GraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Matriz de Adjacência para Grafo")

        # Variáveis globais do programa
        self.selecao = None
        self.roteamento = None
        self.dimensao = None
        self.matrix = []
        self.loaded_config = False   # sinaliza se um arquivo foi carregado externamente

        # Configurações da janela
        self.setup_ui()

    def setup_ui(self):
        # global font and material design theme using ttk styles
        # use tuple for option_add to avoid Tcl interpreting space-separated words as separate args
        self.root.option_add('*Font', ('Segoe UI', 10))
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        # colours from Material Design
        primary = '#6200EE'
        primary_dark = '#3700B3'
        accent = '#03DAC6'
        bg = '#FFFFFF'
        fg = '#000000'

        style.configure('Material.TButton', background=primary, foreground='white', font=('Segoe UI', 10, 'bold'),
                        padding=6, borderwidth=0)
        style.map('Material.TButton', background=[('active', primary_dark)])

        style.configure('Material.TLabel', background=bg, foreground=fg, font=('Segoe UI', 12))
        style.configure('Material.TCheckbutton', background=bg, foreground=fg, font=('Segoe UI', 10))
        style.configure('Material.TEntry', fieldbackground='#f5f5f5', padding=5)
        style.configure('Material.TCombobox', fieldbackground='#f5f5f5', padding=5)

        # Definir o tamanho inicial da janela (largura x altura)
        largura = 400
        altura = 550
        # centralizar
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - largura) // 2
        y = (screen_h - altura) // 2
        self.root.geometry(f"{largura}x{altura}+{x}+{y}")
        self.root.configure(bg=bg)
        self.root.resizable(True, True)  # permitir redimensionamento
        self.root.minsize(400, 550)  # tamanho mínimo para evitar deformação

        # frames para agrupar seções e melhorar alinhamento
        self.frame_top = ttk.Frame(self.root, style='Material.TLabel', padding=10)
        self.frame_top.grid(row=0, column=0, sticky=tk.EW)

        self.frame_body = ttk.Frame(self.root, style='Material.TLabel', padding=10)
        self.frame_body.grid(row=1, column=0, sticky=tk.NSEW)

        self.frame_bottom = ttk.Frame(self.root, style='Material.TLabel', padding=10)
        self.frame_bottom.grid(row=2, column=0, sticky=tk.EW)

        # permitir expansão do corpo
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.frame_body.columnconfigure(0, weight=1)

        # Cabeçalho e botão de carregar
        titulo_top = ttk.Label(self.frame_top, text="Configuração da NoC",
                                style='Material.TLabel', font=('Segoe UI', 18, 'bold'))
        titulo_top.grid(row=0, column=0, sticky=tk.W, pady=5)

        botao_carregar = ttk.Button(self.frame_top, text="📂 Carregar Arquivo de Configuração",
                                    command=self.carregar_arquivo_config, style='Material.TButton')
        botao_carregar.grid(row=1, column=0, sticky=tk.EW, padx=5, pady=5)

        # Rótulo para o título "Métricas"
        rotulo_metricas = ttk.Label(self.frame_body, text="Métricas", style='Material.TLabel',
                                    font=('Segoe UI', 16, 'bold'))
        rotulo_metricas.grid(row=0, column=0, columnspan=2, pady=10, padx=40)

        # Lista de itens para as métricas
        lista_metricas = ["Energia", "Latência", "Tolerância a falha"]

        # Variáveis para armazenar os estados das checkboxes
        self.variaveis_checkbox = [tk.IntVar() for _ in range(len(lista_metricas))]

        # Criar checkboxes para cada item na lista usando estilo material
        for i, item in enumerate(lista_metricas):
            checkbox = ttk.Checkbutton(
                self.frame_body,
                text=item,
                variable=self.variaveis_checkbox[i],
                style='Material.TCheckbutton'
            )
            checkbox.grid(row=i + 1, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=5)

        # Rótulo para o título "Grid"
        # grid size label + entry in a subframe for neatness
        rotulo_grid = ttk.Label(self.frame_body, text="Grid (nxn)", style='Material.TLabel',
                                  font=("Segoe UI", 16, "bold"))
        rotulo_grid.grid(row=4, column=0, columnspan=2, pady=10, padx=40)

        self.entrada_novo_valor = ttk.Entry(self.frame_body, style='Material.TEntry', width=10)
        self.entrada_novo_valor.grid(row=5, column=0, columnspan=2, pady=5, padx=5)

        # Roteamento section
        rotulo_roteamento = ttk.Label(self.frame_body, text="Roteamento", style='Material.TLabel',
                                       font=("Segoe UI", 16, "bold"))
        rotulo_roteamento.grid(row=6, column=0, columnspan=2, pady=10, padx=40)

        opcoes = ["XY", "XYX", "Negative First"]
        self.valor_selecionado = tk.StringVar()
        self.combo = ttk.Combobox(self.frame_body, values=opcoes, textvariable=self.valor_selecionado,
                                  state="readonly", style='Material.TCombobox', width=15)
        self.combo.grid(row=7, column=0, columnspan=2, padx=10, pady=5)

        botao_atualizar_valor = ttk.Button(self.frame_bottom, text="Calcular", command=self.atualizar_valores,
                                          style='Material.TButton')
        botao_atualizar_valor.grid(row=0, column=0, padx=5, pady=5)

    def carregar_arquivo_config(self):
        """Carrega um arquivo JSON com configurações (dimensão, métricas, roteamento, matriz)"""
        arquivo = filedialog.askopenfilename(
            title="Selecionar arquivo de configuração",
            filetypes=[("JSON files", "*.json"), ("Todos os arquivos", "*.*")],
            initialdir=os.path.expanduser("~")
        )
        
        if not arquivo:
            return
        
        try:
            with open(arquivo, 'r') as f:
                dados = json.load(f)
            
            # Validar estrutura do arquivo
            if "matriz_adj" not in dados or "grid_size" not in dados:
                messagebox.showerror("Erro", "Arquivo inválido. Deve conter 'matriz_adj' e 'grid_size'.")
                return
            
            self.matrix = dados.get("matriz_adj")
            grid = dados.get("grid_size")

            # basic validation
            if self.matrix is None or not isinstance(self.matrix, list):
                messagebox.showerror("Erro", "Arquivo JSON inválido: matriz_adj ausente ou nula.")
                return
            if any(row is None or not isinstance(row, list) for row in self.matrix):
                messagebox.showerror("Erro", "Arquivo JSON inválido: matriz_adj deve ser uma lista de listas.")
                return
            # Verificar se a matriz é quadrada
            n = len(self.matrix)
            if n == 0:
                messagebox.showerror("Erro", "Matriz vazia.")
                return
            for row in self.matrix:
                if len(row) != n:
                    messagebox.showerror("Erro", "A matriz deve ser quadrada (mesmo número de linhas e colunas).")
                    return
                for val in row:
                    if not isinstance(val, (int, float)):
                        messagebox.showerror("Erro", "Todos os elementos da matriz devem ser números.")
                        return

            if grid is None:
                messagebox.showerror("Erro", "Arquivo JSON inválido: grid_size ausente ou nulo.")
                return
            if isinstance(grid, list):
                try:
                    self.dimensao = tuple(grid)
                except Exception:
                    messagebox.showerror("Erro", "grid_size deve ser lista de dois inteiros.")
                    return
            else:
                try:
                    self.dimensao = (int(grid), int(grid))
                except Exception:
                    messagebox.showerror("Erro", "grid_size deve ser um inteiro ou lista de inteiros.")
                    return

            self.size = len(self.matrix)
            
            # Verificar se o número de tarefas cabe na grid
            max_tarefas = self.dimensao[0] * self.dimensao[1]
            if self.size > max_tarefas:
                messagebox.showerror("Erro", f"Número de tarefas ({self.size}) excede o tamanho da grid ({max_tarefas}).")
                return
            
            # Carregar métricas se existirem (e manter estado em self.selecao)
            if "metricas" in dados:
                met = dados["metricas"]
                # valida tamanho e tipo
                if isinstance(met, list):
                    for i, valor in enumerate(met):
                        if i < len(self.variaveis_checkbox):
                            self.variaveis_checkbox[i].set(valor)
                    # armazena seleção pronta para uso posterior
                    self.selecao = met.copy()
                else:
                    # caso inválido, inicializa com zeros
                    self.selecao = [0] * len(self.variaveis_checkbox)
            else:
                # nenhuma métrica especificada
                self.selecao = [0] * len(self.variaveis_checkbox)

            # Carregar roteamento se existir
            if "roteamento" in dados:
                self.roteamento = dados["roteamento"]
                self.valor_selecionado.set(self.roteamento)

            # Carregar dimensão do grid se existir
            if "grid_size" in dados:
                self.entrada_novo_valor.delete(0, tk.END)
                self.entrada_novo_valor.insert(0, str(self.dimensao[0]))
            
            messagebox.showinfo("Sucesso", "Configurações carregadas com sucesso!")
            self.loaded_config = True
            self.root.destroy()
            self.create_graph()
            
        except json.JSONDecodeError:
            messagebox.showerror("Erro", "Arquivo JSON inválido.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar arquivo: {str(e)}")

    def salvar_config_arquivo(self, dados_entrada):
        """Salva as configurações em um arquivo JSON"""
        arquivo = filedialog.asksaveasfilename(
            title="Salvar configuração como",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Todos os arquivos", "*.*")],
            initialdir=os.path.expanduser("~"),
            initialfile="configuracao.json"
        )
        
        if not arquivo:
            return
        
        try:
            config = {
                "matriz_adj": self.matrix,
                "grid_size": self.dimensao[0],
                "metricas": self.selecao,
                "roteamento": self.roteamento
            }
            
            with open(arquivo, 'w') as f:
                json.dump(config, f, indent=4)
            
            messagebox.showinfo("Sucesso", f"Configuração salva em:\n{arquivo}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar arquivo: {str(e)}")

    def atualizar_valores(self):
        # Seleção valores das Métricas
        self.selecao = [var.get() for var in self.variaveis_checkbox]

        # Seleção do Roteamento
        self.roteamento = self.combo.get()

        # Seleção da dimensão do SoC
        dim = self.entrada_novo_valor.get()
        try:
            self.dimensao = (int(dim), int(dim))
            self.root.destroy()
            self.get_matrix_size()
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira um valor numérico.")

    def _apply_material_theme(self, window):
        # apply same background color to any additional window
        try:
            window.configure(bg='#FFFFFF')
        except Exception:
            pass

    def get_matrix_size(self):
        self.matrix_window = tk.Tk()
        self.matrix_window.title("Entrada da Matriz de Adjacência")
        self._apply_material_theme(self.matrix_window)
        # center and fixed
        self.matrix_window.resizable(False, False)
        sw = self.matrix_window.winfo_screenwidth()
        sh = self.matrix_window.winfo_screenheight()
        w, h = 300, 150
        self.matrix_window.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        
        self.label = ttk.Label(self.matrix_window, text="Insira a dimensão da matriz de adjacência:", style='Material.TLabel')
        self.label.pack(padx=10, pady=5)
        
        self.entry = ttk.Entry(self.matrix_window, style='Material.TEntry')
        self.entry.pack(padx=10, pady=5)
        
        self.button = ttk.Button(self.matrix_window, text="OK", command=self.get_matrix_entries, style='Material.TButton')
        self.button.pack(pady=10)

    def get_matrix_entries(self):
        try:
            self.size = int(self.entry.get())
            if self.size <= 0:
                raise ValueError("Dimensão deve ser maior que 0.")
            
            self.matrix_window.destroy()
            self.matrix_input_window = tk.Tk()
            self.matrix_input_window.title("Entrada da Matriz de Adjacência")
            self._apply_material_theme(self.matrix_input_window)
            self.matrix_input_window.resizable(False, False)
            # size similar to grid to avoid huge blank space
            self.matrix = []
            self.matrix_entry_widgets = []

            # Configurar as linhas e colunas para se expandirem
            for i in range(self.size):
                self.matrix_input_window.rowconfigure(i, weight=1)
                self.matrix_input_window.columnconfigure(i, weight=1)

                row_entries = []
                for j in range(self.size):
                    entry = ttk.Entry(self.matrix_input_window, width=3, style='Material.TEntry')
                    entry.grid(row=i, column=j, padx=20, pady=20, sticky="nsew")
                    row_entries.append(entry)
                self.matrix_entry_widgets.append(row_entries)

            # Configurar o botão de submit
            submit_button = ttk.Button(self.matrix_input_window, text="Submit", command=self.submit_matrix, style='Material.TButton')
            submit_button.grid(row=self.size, columnspan=self.size)

            # Configurar a linha e coluna do botão de submit para expandirem
            self.matrix_input_window.rowconfigure(self.size, weight=1)
            self.matrix_input_window.columnconfigure(0, weight=1)
        except ValueError as e:
            messagebox.showerror("Erro", str(e))


    def submit_matrix(self):
        try:
            self.matrix = []
            for row_entries in self.matrix_entry_widgets:
                row = []
                for entry in row_entries:
                    value = int(entry.get())
                    row.append(value)
                self.matrix.append(row)

            self.size = len(self.matrix)
            
            # Verificar se o número de tarefas cabe na grid
            max_tarefas = self.dimensao[0] * self.dimensao[1]
            if self.size > max_tarefas:
                messagebox.showerror("Erro", f"Número de tarefas ({self.size}) excede o tamanho da grid ({max_tarefas}).")
                return

            self.matrix_input_window.destroy()
            self.create_graph()
            #self.calculate_best_solution() proximo passo
        except ValueError as e:
            messagebox.showerror("Erro", "Por favor, insira valores numéricos válidos.")

    def create_graph(self):
        G = nx.Graph()
        
        for i in range(self.size):
            for j in range(self.size):
                if self.matrix[i][j] != 0:
                    G.add_edge(i, j, weight=self.matrix[i][j])
        
        pos = nx.spring_layout(G)
        edge_labels = nx.get_edge_attributes(G, 'weight')
        
        nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=500, font_size=10, font_weight='bold')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
        plt.savefig("grafo.png", format="PNG")
        plt.show()
        
        self.verificação_da_corretude()


    def verificação_da_corretude(self):
        response = messagebox.askyesno("Confirmação", "O grafo está correto?")
        if response:
            # somente pergunta para salvar se não veio de um arquivo
            if not self.loaded_config:
                salvar = messagebox.askyesno("Salvar Configuração", 
                                            "Deseja salvar a configuração em um arquivo?\n"
                                            "(Você poderá usá-lo posteriormente como entrada)")
                if salvar:
                    self.salvar_config_arquivo(None)
            
            # Prosseguir com o cálculo ou a próxima etapa
            self.mapeamentos()
        else:
            # Reabrir a janela para que o usuário insira a matriz novamente
            self.perguntar_novamente_matrix()


    def perguntar_novamente_matrix(self):
        # Reabre a janela de entrada da matriz sem precisar de self.entry
        self.matrix_input_window = tk.Tk()
        self.matrix_input_window.title("Entrada da Matriz de Adjacência")
        self._apply_material_theme(self.matrix_input_window)
        self.matrix_input_window.resizable(False, False)
        self.matrix = []
        self.matrix_entry_widgets = []

        # Configurar as linhas e colunas para se expandirem
        for i in range(self.size):
            self.matrix_input_window.rowconfigure(i, weight=1)
            self.matrix_input_window.columnconfigure(i, weight=1)

            row_entries = []
            for j in range(self.size):
                entry = ttk.Entry(self.matrix_input_window, width=3, style='Material.TEntry')
                entry.grid(row=i, column=j, padx=20, pady=20, sticky="nsew")
                row_entries.append(entry)
            self.matrix_entry_widgets.append(row_entries)

        # Configurar o botão de submit
        submit_button = ttk.Button(self.matrix_input_window, text="Submit", command=self.submit_matrix, style='Material.TButton')
        submit_button.grid(row=self.size, columnspan=self.size)

        # Configurar a linha e coluna do botão de submit para expandirem
        self.matrix_input_window.rowconfigure(self.size, weight=1)
        self.matrix_input_window.columnconfigure(0, weight=1)

    def mapeamentos(self):
        # antes de usar, assegura que selecao é lista de inteiros
        if not self.selecao or not isinstance(self.selecao, list):
            self.selecao = [0, 0, 0]

        metricas_ativas = sum(self.selecao)

        # ── MÚLTIPLAS MÉTRICAS: usar apenas NSGA-II ──────────────────────────
        if metricas_ativas >= 2:
            try:
                cores_noc9 = Run_NSGA2(
                    self.matrix, self.dimensao[0], self.roteamento,
                    selecao=self.selecao
                )
            except Exception as e:
                print(f"Erro ao executar NSGA-II: {e}")
                cores_noc9 = None

            if cores_noc9 is None:
                cores_noc9 = [['' for _ in range(self.dimensao[0])] for _ in range(self.dimensao[0])]

            print(f"{'en_nsga2':<15} {str(cores_noc9)}")
            melhor_map = cores_noc9

        # ── MÉTRICA ÚNICA: comparar todos os algoritmos ───────────────────────
        else:
            tempo_limite = 20
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(Run_Genetic_Algorithm, 10000, 100, 0.5, self.matrix, self.dimensao[0])
                    cores_noc = future.result(timeout=tempo_limite)
            except concurrent.futures.TimeoutError:
                print(f"Erro: Run_Genetic_Algorithm excedeu o tempo limite de {tempo_limite} segundos.")
                cores_noc = None
            except Exception as e:
                print(f"Erro ao executar Run_Genetic_Algorithm: {e}")
                cores_noc = None

            if cores_noc is None:
                cores_noc = [[0 for _ in range(self.dimensao[0])] for _ in range(self.dimensao[0])]

            try:
                cores_noc2 = Run_Andean_condor(self.matrix, self.dimensao[0])
            except Exception as e:
                cores_noc2 = []

            cores_noc3 = Run_Random(self.matrix, self.dimensao[0])
            cores_noc7 = RunSimulateAnneling(self.matrix, self.dimensao[0], 1000, 0.95, 100)
            cores_noc8 = [['' for _ in range(self.dimensao[1])] for _ in range(self.dimensao[1])]
            cores_noc8 = Run_Cluster_based(cores_noc8, self.matrix)

            if self.selecao[0] == 1:
                # ── Energia ──
                def _en(m):
                    try:    return self.calcular_energia(m)
                    except: return 9999999999999

                energias = {
                    "en_gene":    _en(cores_noc),
                    "en_andean":  _en(cores_noc2),
                    "en_ramdon":  _en(cores_noc3),
                    "en_simu":    _en(cores_noc7),
                    "en_cluster": _en(cores_noc8),
                }
                mapas_noc = {
                    "en_gene":    cores_noc,
                    "en_andean":  cores_noc2,
                    "en_ramdon":  cores_noc3,
                    "en_simu":    cores_noc7,
                    "en_cluster": cores_noc8,
                }
                for nome, energia in energias.items():
                    matriz_str = ", ".join(str(linha) for linha in mapas_noc[nome])
                    print(f"{nome:<15} {energia:<10.2f} {matriz_str}")
                melhor_map = mapas_noc[min(energias, key=energias.get)]

            elif self.selecao[1] == 1:
                # ── Latência ──
                def _lat(m):
                    try:    return Noc(self.dimensao[0], self.roteamento, self.matrix, m).latencia()
                    except: return 9999999999

                latencia = {
                    "en_gene":    _lat(cores_noc),
                    "en_ramdon":  _lat(cores_noc3),
                    "en_simu":    _lat(cores_noc7),
                    "en_cluster": _lat(cores_noc8),
                }
                mapas_noc = {
                    "en_gene":    cores_noc,
                    "en_ramdon":  cores_noc3,
                    "en_simu":    cores_noc7,
                    "en_cluster": cores_noc8,
                }
                for nome, energia in latencia.items():
                    matriz_str = ", ".join(str(linha) for linha in mapas_noc[nome])
                    print(f"{nome:<15} {energia:<10.2f} {matriz_str}")
                melhor_map = mapas_noc[min(latencia, key=latencia.get)]

            elif self.selecao[2] == 1:
                # ── Tolerância ──
                def _tol(m):
                    try:    return self.calcular_tolerancia_falha(m)
                    except: return 9999999999

                tolerancia = {
                    "en_gene":    _tol(cores_noc),
                    "en_andean":  _tol(cores_noc2),
                    "en_ramdon":  _tol(cores_noc3),
                    "en_simu":    _tol(cores_noc7),
                    "en_cluster": _tol(cores_noc8),
                }
                mapas_noc = {
                    "en_gene":    cores_noc,
                    "en_andean":  cores_noc2,
                    "en_ramdon":  cores_noc3,
                    "en_simu":    cores_noc7,
                    "en_cluster": cores_noc8,
                }
                for nome, energia in tolerancia.items():
                    matriz_str = ", ".join(str(linha) for linha in mapas_noc[nome])
                    print(f"{nome:<15} {energia:<10.2f} {matriz_str}")
                melhor_map = mapas_noc[min(tolerancia, key=tolerancia.get)]

            else:
                # Nenhuma métrica selecionada — usa aleatório como fallback
                melhor_map = cores_noc3

        data = {
            "matriz_adj":        self.matrix,
            "melhor_mapeamento": melhor_map,
            "n":                 self.dimensao,
            "roteamento":        self.roteamento,
            "metricas":          self.selecao
        }
        with open('config.json', 'w') as f:
            json.dump(data, f)


    def calcular_energia(self, mapeamento):
        if mapeamento is None:
            raise ValueError("Mapeamento não pode ser None")
        n = len(self.matrix)  # Número de tarefas
        m = len(mapeamento)  # Dimensão da NoC
        valor_final = 0

        for i in range(n):  # Percorre todas as tarefas
            for j in range(n):  # Garante que a matriz seja percorrida uma única vez (i, j) != (j, i)
                bandwidth = self.matrix[i][j]
                if bandwidth > 0 :  # Se há comunicação entre as tarefas i e j
                    # Encontra a posição de i no mapeamento
                    ix, iy = [(k, l) for k in range(m) for l in range(m) if mapeamento[k][l] == i][0]
                    jx, jy = [(k, l) for k in range(m) for l in range(m) if mapeamento[k][l] == j][0]
                    # Calcula a distância Manhattan
                    man_dist = abs(ix - jx) + abs(iy - jy)
                    # Acumula o valor da energia total
                    valor_final += bandwidth * man_dist

        return valor_final
    
    def calcular_tolerancia_falha(self, matriz):
        if matriz is None:
            raise ValueError("Matriz de mapeamento não pode ser None")
        # Direções para as células adjacentes (cima, baixo, esquerda, direita)
        direcoes = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        tolerancia = 0

        # Itera sobre cada célula da matriz
        for i in range(len(matriz)):
            for j in range(len(matriz[i])):
                # Verifica se a célula contém uma tarefa (número diferente de 0)
                if matriz[i][j] != 0:
                    # Verifica se há células adjacentes vazias que têm uma tarefa adjacente
                    for dx, dy in direcoes:
                        x, y = i + dx, j + dy
                        # Verifica se a posição está dentro dos limites da matriz
                        if 0 <= x < len(matriz) and 0 <= y < len(matriz[0]):
                            # Se a célula adjacente estiver vazia (0)
                            if matriz[x][y] != 0:
                                tolerancia += 1
                                
        return tolerancia
    

if __name__ == "__main__":
    root = tk.Tk()
    app = GraphApp(root)
    root.mainloop()
    sleep(1)
    from Tela import *