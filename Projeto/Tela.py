import tkinter as tk
from tkinter import ttk
import json
from Noc import *
from PIL import Image, ImageTk
import os


# Dicionário global para armazenar pacotes
pacotes = {}

def calcular_escala(n):
    painel_w = largura_canvas * 0.22
    area_w   = largura_canvas - painel_w
    tq = int(min(area_w, altura_canvas * 0.90) / (2 * n + 1))
    tq  = max(tq, 20)
    esp = tq
    tqp = max(14, int(tq * 0.57))
    tr  = max(5,  int(tq * 0.21))
    total  = n * (tq + esp) - esp
    margem = esp
    ox = int((area_w - total) // 2)
    ox = max(ox, margem + tqp // 2 + 4)
    oy = int((altura_canvas - total) // 2)
    oy = max(oy, margem + tqp // 2 + 4)
    px      = int(largura_canvas - painel_w // 2)
    img_sz  = int(min(painel_w * 0.85, altura_canvas * 0.22))
    cel_map = max(12, int((painel_w * 0.70) / n))
    raio_pacote  = max(7, int(tq * 0.18))
    passo_celula = tq + esp
    return dict(tq=tq, esp=esp, tqp=tqp, tr=tr, total=total,
                ox=ox, oy=oy, px=px, img_sz=img_sz, cel_map=cel_map,
                raio_pacote=raio_pacote, passo_celula=passo_celula)


# Função para mover o pacote em uma direção (N, S, L, O) após chegar ao centro maior
def mover_pacote_fase2(x_inicial, y_inicial, x_final, y_final, passo, pacote_oval, pacote_texto):
    x = x_inicial
    y = y_inicial
    dx = (x_final - x_inicial) / passo
    dy = (y_final - y_inicial) / passo

    def animar():
        nonlocal x, y
        if abs(x - x_final) > abs(dx) or abs(y - y_final) > abs(dy):
            canvas.move(pacote_oval, dx, dy)
            canvas.move(pacote_texto, dx, dy)
            x += dx
            y += dy
            janela.after(15, animar)
        '''
        else:
            # corrige erro de ponto flutuante: snap para posição exata
            coords = canvas.coords(pacote_oval)
            cx_atual = (coords[0] + coords[2]) / 2
            cy_atual = (coords[1] + coords[3]) / 2
            canvas.move(pacote_oval, x_final - cx_atual, y_final - cy_atual)
            canvas.move(pacote_texto, x_final - cx_atual, y_final - cy_atual)
        '''
        

    animar()

# Função para mover o pacote do quadrado menor para o quadrado maior
def mover_pacote_fase1(x_inicial, y_inicial, x_final, y_final, pacote_oval, pacote_texto, id_pacote, direcao):
    x = x_inicial
    y = y_inicial
    dx = (x_final - x_inicial) / 50
    dy = (y_final - y_inicial) / 50

    def animar():
        nonlocal x, y
        if abs(x - x_final) > abs(dx) or abs(y - y_final) > abs(dy):
            canvas.move(pacote_oval, dx, dy)
            canvas.move(pacote_texto, dx, dy)
            x += dx
            y += dy
            janela.after(15, animar)
        else:
            # Quando o pacote chegar ao centro do quadrado maior, iniciar a segunda fase de movimento
            mover_pacote_para_direcao(x_final, y_final, pacote_oval, pacote_texto, id_pacote, direcao)

    animar()

# Função para definir a próxima célula com base na direção (N, S, L, O)
def mover_pacote_para_direcao(x_inicial, y_inicial, pacote_oval, pacote_texto, id_pacote, direcao):
    e = calcular_escala(tam[0])
    p = e["passo_celula"]
    if direcao == "Sul":
        x_final, y_final = x_inicial, y_inicial - p
    elif direcao == "Norte":
        x_final, y_final = x_inicial, y_inicial + p
    elif direcao == "Oeste":
        x_final, y_final = x_inicial + p, y_inicial
    elif direcao == "Leste":
        x_final, y_final = x_inicial - p, y_inicial
    elif direcao == "Processador":
        orig = dicionario_pacotes[str(id_pacote)]["i"]
        cpu_i, cpu_j = orig
        x_final, y_final = centros_menores[cpu_i][cpu_j]
    else:
        x_final, y_final = x_inicial, y_inicial
    mover_pacote_fase2(x_inicial, y_inicial, x_final, y_final, 50, pacote_oval, pacote_texto)

def encontrar_posicao_menor(id_pacote):
    i, j = divmod(id_pacote - 1, tam[0])  # Assumindo que os pacotes estão indexados a partir de 1
    return centros_menores[i][j]  # Ajuste conforme a sua estrutura de dados

# Funcao para desenhar a matriz de quadrados
def desenhar_matriz(n):
    global imagem_tk
    map_title_y = 0
    e = calcular_escala(n)
    tq  = e["tq"];  esp = e["esp"];  tqp = e["tqp"];  tr = e["tr"]
    ox  = e["ox"];  oy  = e["oy"];   px  = e["px"]
    img_sz = e["img_sz"];  cel_map = e["cel_map"]

    centros_maiores = [[None]*n for _ in range(n)]
    centros_menores = [[None]*n for _ in range(n)]
    font_port = ("Arial", max(7, tr-3), "bold")

    for i in range(n):
        for j in range(n):
            x1 = j*(tq+esp)+ox;  y1 = i*(tq+esp)+oy
            x2 = x1+tq;          y2 = y1+tq
            cx = (x1+x2)//2;     cy = (y1+y2)//2
            centros_maiores[i][j] = (cx, cy)
            canvas.create_rectangle(x1, y1, x2, y2, fill="lightblue")
            canvas.create_rectangle(cx-tr//2, y1, cx+tr//2, y1+tr, fill="gray")
            canvas.create_text(cx, y1+tr//2, text="N", fill="black", font=font_port)
            canvas.create_rectangle(cx-tr//2, y2-tr, cx+tr//2, y2, fill="gray")
            canvas.create_text(cx, y2-tr//2, text="S", fill="black", font=font_port)
            canvas.create_rectangle(x2-tr, cy-tr//2, x2, cy+tr//2, fill="gray")
            canvas.create_text(x2-tr//2, cy, text="L", fill="black", font=font_port)
            canvas.create_rectangle(x1, cy-tr//2, x1+tr, cy+tr//2, fill="gray")
            canvas.create_text(x1+tr//2, cy, text="O", fill="black", font=font_port)
            if j < n-1:
                canvas.create_line(x2, cy, x2+esp, cy, width=2)
            if i < n-1:
                canvas.create_line(cx, y2, cx, y2+esp, width=2)
            cpu_cx = x1 - esp//2;  cpu_cy = y1 - esp//2
            canvas.create_line(x1, y1, cpu_cx, cpu_cy, width=2)
            centros_menores[i][j] = (cpu_cx, cpu_cy)
            canvas.create_rectangle(cpu_cx-tqp//2, cpu_cy-tqp//2,
                                    cpu_cx+tqp//2, cpu_cy+tqp//2, fill="orange")

    py_base = int(altura_canvas * 0.05)
    canvas.create_text(px, py_base, text="Grafo do Problema:", fill="black",
        font=("Arial", max(9, int(img_sz*0.07)), "bold"), anchor="n")
    try:
        img1 = Image.open("grafo.png")
        imagem_tk = ImageTk.PhotoImage(img1.resize((img_sz, img_sz)))
        canvas.create_image(px, py_base + int(altura_canvas*0.04) + img_sz//2, image=imagem_tk)
        img_y = py_base + int(altura_canvas*0.04) + img_sz
    except Exception:
        img_y = py_base + int(altura_canvas*0.04) + img_sz
        canvas.create_text(px, img_y, text="[grafo.png nao encontrado]", fill="gray", font=("Arial",9))

    rot_y = img_y + int(altura_canvas*0.03)
    canvas.create_text(px, rot_y, text=f"Roteamento: {roteamento}", fill="black",
        font=("Arial", max(9, int(img_sz*0.07)), "bold"), anchor="n")

    cpu_leg_y = rot_y + int(altura_canvas*0.07)
    cpu_box = max(20, int(img_sz*0.18))
    canvas.create_rectangle(px-cpu_box//2, cpu_leg_y-cpu_box//2,
                            px+cpu_box//2, cpu_leg_y+cpu_box//2, fill="orange")
    canvas.create_text(px, cpu_leg_y, text="CPU", fill="black",
        font=("Arial", max(8, int(cpu_box*0.30)), "bold"))

    map_title_y = cpu_leg_y + cpu_box//2 + int(altura_canvas*0.04)
    canvas.create_text(px, map_title_y, text="Melhor Mapeamento:", fill="black",
        font=("Arial", max(9, int(img_sz*0.07)), "bold"), anchor="n")

    gap = max(3, int(cel_map*0.15))
    mat_x0 = px - (n*cel_map+(n-1)*gap)//2
    mat_y0 = map_title_y + int(altura_canvas*0.04)
    font_map = ("Arial", max(7, int(cel_map*0.45)), "bold")
    for i in range(n):
        for j in range(n):
            xm = mat_x0 + j*(cel_map+gap);  ym = mat_y0 + i*(cel_map+gap)
            canvas.create_rectangle(xm, ym, xm+cel_map, ym+cel_map, fill="lightgreen")
            canvas.create_text(xm+cel_map//2, ym+cel_map//2,
                text=f"{melhor_mapeamento[i][j]}", fill="black", font=font_map)

    try:
        with open("config.json", "r") as f:
            _cfg = json.load(f)
        _metricas_ativas = sum(_cfg.get("metricas", []))
    except Exception:
        _metricas_ativas = 0

    if _metricas_ativas > 1 and os.path.exists("pareto_front.png"):
        gap = max(3, int(cel_map*0.15))
        mat_y0 = map_title_y + int(altura_canvas*0.04)
        btn_y = mat_y0 + n*(cel_map + gap) + int(altura_canvas*0.03)
        btn_w = max(80, int(cel_map * n * 0.9))
        btn_h = max(20, int(altura_canvas * 0.04))
        pareto_btn = canvas.create_rectangle(
            px - btn_w//2, btn_y,
            px + btn_w//2, btn_y + btn_h,
            fill="#6200EE", outline=""
        )
        pareto_txt = canvas.create_text(
            px, btn_y + btn_h//2,
            text="Ver Frente de Pareto",
            fill="white", font=("Arial", max(7, int(btn_h*0.45)), "bold")
        )
        def abrir_pareto(event):
            import subprocess, sys
            subprocess.Popen([sys.executable, "-c",
                "from PIL import Image; Image.open('pareto_front.png').show()"])
        canvas.tag_bind(pareto_btn, "<Button-1>", abrir_pareto)
        canvas.tag_bind(pareto_txt, "<Button-1>", abrir_pareto)
        

    return centros_maiores, centros_menores



# Função para criar pacotes e alocá-los com base no mapeamento e matriz de adjacência
def criar_pacotes_e_alocar():
    e = calcular_escala(tam[0])
    raio = e["raio_pacote"]
    font_pacote = ("Arial", max(7, raio-2), "bold")
    id_pacote = 0
    for i in range(len(matrix_adj)):
        for j in range(len(matrix_adj[i])):
            if matrix_adj[i][j] > 0:  # Verifica se há comunicação entre i e j
                origem = encontrar_posicao(i)  # +1 porque as tarefas no mapeamento começam em 1
                destino = encontrar_posicao(j)
                
                if origem and destino:
                    # Adicionar ao dicionario_pacotes
                    dicionario_pacotes[str(id_pacote)] = {
                        "posicao_inicial": i,
                        "posicao_final": j,
                        "i": origem,
                        "f": destino
                    }
                    centro_menor_origem = centros_menores[origem[0]][origem[1]]
                    
                    # Criar pacote oval e texto no centro menor da origem
                    pacote_oval = canvas.create_oval(
                        centro_menor_origem[0] - raio,
                        centro_menor_origem[1] - raio,
                        centro_menor_origem[0] + raio,
                        centro_menor_origem[1] + raio,
                        fill="red"
                    )
                    pacote_texto = canvas.create_text(
                        centro_menor_origem[0], centro_menor_origem[1],
                        text=str(f'{dicionario_pacotes[str(id_pacote)]["posicao_inicial"]},{dicionario_pacotes[str(id_pacote)]["posicao_final"]}'), fill="white", font=font_pacote
                    )
                    qtd_movimentos = 0
                    
                    # Armazena o pacote no dicionário usando o ID como chave
                    pacotes[id_pacote] = (pacote_oval, pacote_texto,qtd_movimentos)
                    # Incrementar o ID para o próximo pacote
                    id_pacote += 1


# Função para encontrar a posição de uma tarefa no mapeamento
def encontrar_posicao(tarefa):
    for i in range(len(melhor_mapeamento)):
        for j in range(len(melhor_mapeamento[i])):
            if melhor_mapeamento[i][j] == tarefa:
                return (i, j)
    return None


# função para animar um pacote com base no dicionário de controle
def animar_pacote():
    global direcoes , arbitro, id_texto_arbitro, animando, after_id
    global chegos_total, perdidos_total 
    animando = True

    direcoes = noc.rodar(2)

    noc.ajusta_pacotes_chegos()      
    noc.ajusta_pacotes_perdido()  

    chegos_total = noc.total_pacotes_chegos[-1]      
    perdidos_total = noc.total_pacotes_perdidos[-1]

    #print(f"{noc.total_pacotes_chegos}  {noc.total_pacotes_perdidos}")

    desenhar_metricas()   

    #ajustar árbitro
    arbitro += 1
    lista_Árbitro = [ "Oeste", "Cpu", "Norte", "Leste", "Sul"]

    # Remover texto antigo do árbitro, se existir
    try:
        if id_texto_arbitro:
            canvas.delete(id_texto_arbitro)
    except NameError:
        pass

    # Adicionar novo texto do árbitro e armazenar o ID
    id_texto_arbitro = canvas.create_text(
        largura_canvas // 2, 20,
        text=f"Árbitro: {lista_Árbitro[arbitro % 5]}",
        fill="black", font=("Arial", 12, "bold"), anchor="center"
    )
    
    # Passa por todos os pacotes que possuem uma direção definida no dicionário de direções
    for id_pacote, direcao in direcoes.items():
        if id_pacote in pacotes:  # Verifica se o pacote com o ID correspondente existe
            pacote_oval, pacote_texto, qtd_movimentos = pacotes[id_pacote]

            # Determinar a célula atual do pacote com base no ID
            origem = dicionario_pacotes[str(id_pacote)]["i"]

            if origem:

                i, j = origem  # Pega a posição da célula no mapeamento

                # Pega as posições do centro do quadrado menor e do quadrado maior
                centro_menor = centros_menores[i][j]
                centro_maior = centros_maiores[i][j]

                if qtd_movimentos == 0:
                    # Movimenta o pacote da fase 1 (do menor para o maior)

                    mover_pacote_fase1(
                        centro_menor[0], centro_menor[1], 
                        centro_maior[0], centro_maior[1], 
                        pacote_oval, pacote_texto, 
                        id_pacote, direcao
                    )
                    qtd_movimentos += 1
                    pacotes[id_pacote] = (pacote_oval, pacote_texto, qtd_movimentos)
                
                else:
                    # Movimenta o pacote na fase 2, para a próxima célula

                    mover_pacote_para_direcao(
                        centro_maior[0], centro_maior[1], 
                        pacote_oval, pacote_texto, 
                        id_pacote, direcao
                    )
                    qtd_movimentos += 1
                    pacotes[id_pacote] = (pacote_oval, pacote_texto, qtd_movimentos)

                    # Atualizar posição atual
                    i, j = origem
                    n_dim = tam[0]
                    if direcao == "Sul":
                        new_i, new_j = min(i + 1, n_dim - 1), j
                    elif direcao == "Norte":
                        new_i, new_j = max(i - 1, 0), j
                    elif direcao == "Leste":
                        new_i, new_j = i, min(j + 1, n_dim - 1)
                    elif direcao == "Oeste":
                        new_i, new_j = i, max(j - 1, 0)
                    elif direcao == "Processador":
                        new_i, new_j = i, j
                    dicionario_pacotes[str(id_pacote)]["i"] = (new_i, new_j)

    # Não continuar automaticamente, aguardar próximo passo


def parar_animacao():
    global animando, after_id
    animando = False
    if after_id:
        canvas.after_cancel(after_id)
        after_id = None

def iniciar_auto():
    global animando
    animando = True
    animar_auto()

def animar_auto():
    global after_id
    animar_pacote()
    if animando:
        after_id = canvas.after(3000, animar_auto)

def voltar():
    janela.destroy()

def recomecar():
    global pacotes, dicionario_pacotes, arbitro, animando, after_id, centros_maiores, centros_menores

    # Parar qualquer animação em andamento
    animando = False
    if after_id:
        canvas.after_cancel(after_id)
        after_id = None

    # Resetar estado
    arbitro = 0
    pacotes = {}
    dicionario_pacotes = {}

    # Recriar o objeto Noc do zero
    Pacote.resetar_contador()
    noc_novo = Noc(tam[0], roteamento, matrix_adj, melhor_mapeamento)
    
    # Atualizar a referência global
    globals()['noc'] = noc_novo  # ou declare noc como global no topo e use: global noc; noc = Noc(...)

    # Recarregar dicionario_pacotes a partir do novo noc
    for i in range(tam[0]):
        for j in range(tam[0]):
            lista_pacotes = noc_novo.matriz_roteadores[i][j].buffers["Processador"]
            if lista_pacotes:
                for k in range(len(lista_pacotes)):
                    pacote_generico = lista_pacotes[k]
                    dicionario_pacotes[str(pacote_generico.id)] = {
                        "posicao_inicial": melhor_mapeamento[pacote_generico.posicao_inicial[0]][pacote_generico.posicao_inicial[1]],
                        "posicao_final": melhor_mapeamento[pacote_generico.posicao_destino[0]][pacote_generico.posicao_destino[1]],
                        "i": (pacote_generico.posicao_inicial[0], pacote_generico.posicao_inicial[1]),
                        "f": (pacote_generico.posicao_destino[0], pacote_generico.posicao_destino[1])
                    }

    # Limpar e redesenhar o canvas
    canvas.delete("all")
    centros_maiores, centros_menores = desenhar_matriz(tam[0])
    criar_pacotes_e_alocar()
    desenhar_metricas() 


id_metricas = {"chegos": None, "perdidos": None, "titulo": None}

def desenhar_metricas():
    global id_metricas
    e = calcular_escala(tam[0])
    px = e["px"]
    cel_map = e["cel_map"]
    gap = max(3, int(cel_map * 0.15))
    n = tam[0]

    img_sz = e["img_sz"]
    py_base = int(altura_canvas * 0.05)
    img_y = py_base + int(altura_canvas * 0.04) + img_sz
    rot_y = img_y + int(altura_canvas * 0.03)
    cpu_leg_y = rot_y + int(altura_canvas * 0.07)
    cpu_box = max(20, int(img_sz * 0.18))
    map_title_y = cpu_leg_y + cpu_box // 2 + int(altura_canvas * 0.04)
    mat_y0 = map_title_y + int(altura_canvas * 0.04)
    mat_bottom = mat_y0 + n * (cel_map + gap)

    btn_h = max(20, int(altura_canvas * 0.04))
    metricas_y = mat_bottom + btn_h + 30

    font_titulo = ("Arial", max(9, int(img_sz * 0.07)), "bold")
    font_valor  = ("Arial", max(9, int(img_sz * 0.07)), "normal")
    linha_h = max(16, int(img_sz * 0.09))

    for key in id_metricas:
        if id_metricas[key]:
            canvas.delete(id_metricas[key])

    id_metricas["titulo"] = canvas.create_text(
        px, metricas_y,
        text="Métricas:", fill="black",
        font=font_titulo, anchor="n"
    )
    id_metricas["chegos"] = canvas.create_text(
        px, metricas_y + linha_h,
        text=f"✔ Chegados: {chegos_total}", fill="#2e7d32",
        font=font_valor, anchor="n"
    )
    id_metricas["perdidos"] = canvas.create_text(
        px, metricas_y + linha_h * 2,
        text=f"✘ Perdidos: {perdidos_total}", fill="#c62828",
        font=font_valor, anchor="n"
    )
    
def carregar_config_json():
    with open('config.json', 'r') as f:
        config = json.load(f)

    # ensure required keys exist and are not None
    for key in ('matriz_adj', 'melhor_mapeamento', 'n', 'roteamento'):
        if key not in config or config[key] is None:
            raise ValueError(f"Chave '{key}' ausente ou nula no config.json")

    # additional sanity checks
    if not isinstance(config['matriz_adj'], list) or not all(isinstance(r, list) for r in config['matriz_adj']):
        raise ValueError("matriz_adj deve ser uma lista de listas")
    if not isinstance(config['melhor_mapeamento'], list):
        raise ValueError("melhor_mapeamento inválido")

    return config['matriz_adj'], config['melhor_mapeamento'], config['n'], config['roteamento']

global arbitro, chegos_total, perdidos_total
arbitro = 0
chegos_total = 0
perdidos_total = 0

global noc  

# Criação da janela principal e do canvas
janela = tk.Tk()
largura_canvas = 1200
altura_canvas = 800
canvas = tk.Canvas(janela, width=largura_canvas, height=altura_canvas, bg='white')
canvas.grid(row=0, column=0, sticky=tk.NSEW)  # usar grid para layout

# configurar grid weights
janela.rowconfigure(0, weight=1)
janela.columnconfigure(0, weight=1)

# centralizar e permitir redimensionamento
screen_w = janela.winfo_screenwidth()
screen_h = janela.winfo_screenheight()
x = (screen_w - largura_canvas) // 2
y = (screen_h - altura_canvas) // 2
janela.geometry(f"{largura_canvas}x{altura_canvas}+{x}+{y}")
janela.resizable(True, True)  # permitir redimensionamento
janela.minsize(800, 600)  # tamanho mínimo para evitar deformação

# função para redesenhar ao redimensionar
animando = False  # flag para animação ativa
after_id = None  # ID do after para cancelar animação

_resize_job = None
def on_resize(event):
    global largura_canvas, altura_canvas, animando, after_id, centros_maiores, centros_menores, _resize_job
    if event.widget != janela:
        return
    if animando:
        animando = False
        if after_id:
            canvas.after_cancel(after_id)
            after_id = None
    if _resize_job:
        janela.after_cancel(_resize_job)
    largura_canvas = event.width
    altura_canvas  = max(1, event.height - 60)
    canvas.config(width=largura_canvas, height=altura_canvas)
    def _do_redraw():
        global centros_maiores, centros_menores
        canvas.delete("all")
        centros_maiores, centros_menores = desenhar_matriz(tam[0])
        criar_pacotes_e_alocar()
        desenhar_metricas()  
    _resize_job = janela.after(150, _do_redraw)


# Armazena as informações passadas
try:
    matrix_adj, melhor_mapeamento , tam , roteamento = carregar_config_json()
except FileNotFoundError:
    # Valores padrão se config.json não existir
    matrix_adj = [[0,1,0],[1,0,1],[0,1,0]]
    melhor_mapeamento = [[0,1,2],[3,4,5],[6,7,8]]
    tam = [3,3]
    roteamento = "XY"
Pacote.resetar_contador()
noc = Noc(tam[0] ,roteamento, matrix_adj, melhor_mapeamento)


global dicionario_pacotes
dicionario_pacotes = {}
for i in range(tam[0]):
           for j in range(tam[0]):
               lista_pacotes = noc.matriz_roteadores[i][j].buffers["Processador"]
               if lista_pacotes:
                   for k in range(len(lista_pacotes)):
                        pacote_generico = lista_pacotes[k]
                        dicionario_pacotes[str(pacote_generico.id)] = {
                        "posicao_inicial": melhor_mapeamento[pacote_generico.posicao_inicial[0]][pacote_generico.posicao_inicial[1]],
                        "posicao_final": melhor_mapeamento[pacote_generico.posicao_destino[0]][pacote_generico.posicao_destino[1]],
                        "i" : (pacote_generico.posicao_destino[0],pacote_generico.posicao_destino[1]),
                        "f":(pacote_generico.posicao_destino[0],pacote_generico.posicao_destino[1])
                        }

               
centros_maiores, centros_menores = desenhar_matriz(tam[0])
criar_pacotes_e_alocar()


# Adicionar botão para iniciar a animação
# button using ttk style to match material design
style = ttk.Style()
try:
    style.theme_use('clam')
except Exception:
    pass
style.configure('Material.TButton', background='#6200EE', foreground='white', font=('Segoe UI', 10, 'bold'), padding=6, borderwidth=0)
style.map('Material.TButton', background=[('active', '#3700B3')])

janela.configure(bg='#FFFFFF')

# Configurar grid para a janela
janela.rowconfigure(0, weight=1)
janela.columnconfigure(0, weight=1)

# Canvas ocupa a maior parte
canvas.grid(row=0, column=0, sticky='nsew')

# Frame para botões na parte inferior
frame_botoes = tk.Frame(janela, bg='#FFFFFF')
frame_botoes.grid(row=1, column=0, sticky='ew', pady=10)

# Configurar centralização
frame_botoes.columnconfigure(0, weight=1)
frame_botoes.columnconfigure(1, weight=0)
frame_botoes.columnconfigure(2, weight=0)
frame_botoes.columnconfigure(3, weight=0)
frame_botoes.columnconfigure(4, weight=1)

botao_animar = ttk.Button(frame_botoes, text="Próximo Passo", command=animar_pacote, style='Material.TButton')
botao_animar.grid(row=0, column=1, padx=5)

botao_auto = ttk.Button(frame_botoes, text="Iniciar Automático", command=iniciar_auto, style='Material.TButton')
botao_auto.grid(row=0, column=2, padx=5)

botao_parar = ttk.Button(frame_botoes, text="Parar", command=parar_animacao, style='Material.TButton')
botao_parar.grid(row=0, column=3, padx=5)

botao_recomecar = ttk.Button(frame_botoes, text="Recomeçar", command=recomecar, style='Material.TButton')
botao_recomecar.grid(row=0, column=4, padx=5)

botao_voltar = ttk.Button(frame_botoes, text="Voltar", command=voltar, style='Material.TButton')
botao_voltar.grid(row=0, column=5, padx=5)

janela.bind("<Configure>", on_resize)

janela.mainloop()