import random
import matplotlib
matplotlib.use('TkAgg')   # backend compatível com tkinter
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 — necessário para plot 3D


# ─────────────────────────────────────────────────────────────
# Funções de métricas
# ─────────────────────────────────────────────────────────────

def calcular_energia(mapeamento, matrix, dimensao):
    n = len(matrix)
    m = len(mapeamento)
    valor_final = 0
    # Cache de posições para não recalcular O(n²·m²)
    pos = {}
    for k in range(m):
        for l in range(m):
            if mapeamento[k][l] != '':
                pos[mapeamento[k][l]] = (k, l)

    for i in range(n):
        for j in range(n):
            bw = matrix[i][j]
            if bw > 0 and i in pos and j in pos:
                ix, iy = pos[i]
                jx, jy = pos[j]
                valor_final += bw * (abs(ix - jx) + abs(iy - jy))
    return valor_final


def calcular_latencia(mapeamento, matrix, dimensao, roteamento):
    """
    Estimativa de latência: hop count máximo ponderado pela bandwidth.
    Diferente de energia (que soma todos os pares), aqui pegamos o maior
    custo individual — bottleneck de comunicação.
    """
    n = len(matrix)
    m = len(mapeamento)
    pos = {}
    for k in range(m):
        for l in range(m):
            if mapeamento[k][l] != '':
                pos[mapeamento[k][l]] = (k, l)

    max_custo = 0
    for i in range(n):
        for j in range(n):
            bw = matrix[i][j]
            if bw > 0 and i in pos and j in pos:
                ix, iy = pos[i]
                jx, jy = pos[j]
                hops = abs(ix - jx) + abs(iy - jy)
                custo = bw * hops   # latência proporcional a hops * bandwidth
                if custo > max_custo:
                    max_custo = custo
    return float(max_custo)


def calcular_tolerancia_falha(mapeamento, matrix, dimensao):
    """
    Conta células adjacentes livres ao redor de cada tarefa.
    Quanto maior, maior a capacidade de realocar ou redirecionar em caso de falha.
    Retornamos negativo porque o NSGA-II minimiza todos os objetivos.
    """
    direcoes = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    tolerancia = 0
    for i in range(len(mapeamento)):
        for j in range(len(mapeamento[i])):
            if mapeamento[i][j] != '':
                for dx, dy in direcoes:
                    x, y = i + dx, j + dy
                    if 0 <= x < len(mapeamento) and 0 <= y < len(mapeamento[0]):
                        if mapeamento[x][y] == '':
                            tolerancia += 1
    return tolerancia


# ─────────────────────────────────────────────────────────────
# Classe Indivíduo
# ─────────────────────────────────────────────────────────────

class Individuo:
    def __init__(self, mapeamento, matrix, dimensao, roteamento, selecao):
        self.mapeamento = mapeamento
        self.matrix = matrix
        self.dimensao = dimensao
        self.roteamento = roteamento
        self.selecao = selecao
        self.objetivos = []

        if selecao[0]:   # Energia (minimizar)
            self.objetivos.append(calcular_energia(mapeamento, matrix, dimensao))
        if selecao[1]:   # Latência (minimizar)
            self.objetivos.append(calcular_latencia(mapeamento, matrix, dimensao, roteamento))
        if selecao[2]:   # Tolerância (maximizar → negativo para minimizar)
            self.objetivos.append(-calcular_tolerancia_falha(mapeamento, matrix, dimensao))

        # Atributos de dominância — resetados antes de cada sort
        self.dominancia_count = 0
        self.dominados = []
        self.rank = 0
        self.crowding_distance = 0

    def dominates(self, other):
        better_or_equal = all(s <= o for s, o in zip(self.objetivos, other.objetivos))
        better_in_one   = any(s <  o for s, o in zip(self.objetivos, other.objetivos))
        return better_or_equal and better_in_one

    def reset_dominancia(self):
        """Deve ser chamado antes de cada fast_non_dominated_sort."""
        self.dominancia_count = 0
        self.dominados = []
        self.rank = 0
        self.crowding_distance = 0


# ─────────────────────────────────────────────────────────────
# NSGA-II — operadores
# ─────────────────────────────────────────────────────────────

def fast_non_dominated_sort(population):
    # BUGFIX: resetar estado de dominância antes de recalcular
    for p in population:
        p.reset_dominancia()

    fronts = [[]]
    for p in population:
        for q in population:
            if p is q:
                continue
            if p.dominates(q):
                p.dominados.append(q)
            elif q.dominates(p):
                p.dominancia_count += 1
        if p.dominancia_count == 0:
            p.rank = 0
            fronts[0].append(p)

    i = 0
    while fronts[i]:
        Q = []
        for p in fronts[i]:
            for q in p.dominados:
                q.dominancia_count -= 1
                if q.dominancia_count == 0:
                    q.rank = i + 1
                    Q.append(q)
        i += 1
        fronts.append(Q)
    return fronts[:-1]


def calculate_crowding_distance(front):
    if not front:
        return
    n_obj = len(front[0].objetivos)
    for ind in front:
        ind.crowding_distance = 0

    for obj in range(n_obj):
        front.sort(key=lambda x: x.objetivos[obj])
        front[0].crowding_distance  = float('inf')
        front[-1].crowding_distance = float('inf')
        if len(front) > 2:
            obj_range = front[-1].objetivos[obj] - front[0].objetivos[obj]
            if obj_range > 0:
                for k in range(1, len(front) - 1):
                    front[k].crowding_distance += (
                        front[k+1].objetivos[obj] - front[k-1].objetivos[obj]
                    ) / obj_range


def generate_random_mapping(dimensao, num_tarefas):
    tarefas = list(range(num_tarefas))
    random.shuffle(tarefas)
    
    # Todas as posições da matriz
    todas_posicoes = [(i, j) for i in range(dimensao) for j in range(dimensao)]
    # Escolhe aleatoriamente quais células vão receber tarefas
    posicoes_escolhidas = random.sample(todas_posicoes, num_tarefas)
    
    mapeamento = [['' for _ in range(dimensao)] for _ in range(dimensao)]
    for idx, (i, j) in enumerate(posicoes_escolhidas):
        mapeamento[i][j] = tarefas[idx]
    
    return mapeamento


def crossover(parent1, parent2, dimensao):
    # Extrair só as tarefas e suas posições
    def extrair(parent):
        pos, tar = [], []
        for i in range(dimensao):
            for j in range(dimensao):
                if parent[i][j] != '' and parent[i][j] != -1:
                    pos.append((i, j))
                    tar.append(parent[i][j])
        return pos, tar

    pos1, tar1 = extrair(parent1)
    pos2, tar2 = extrair(parent2)
    n = len(tar1)
    if n < 2:
        return [row[:] for row in parent1], [row[:] for row in parent2]

    ponto1, ponto2 = sorted(random.sample(range(n), 2))

    # PMX só nas tarefas
    def pmx_tarefas(t1, t2, p1, p2):
        filho_tar = [None] * n
        filho_tar[p1:p2] = t1[p1:p2]
        segmento = set(t1[p1:p2])
        pointer = p2
        for gene in t2:
            if gene not in segmento:
                if pointer >= n:
                    pointer = 0
                while filho_tar[pointer] is not None:
                    pointer += 1
                    if pointer >= n:
                        pointer = 0
                filho_tar[pointer] = gene
                pointer += 1
        return filho_tar

    tar_filho1 = pmx_tarefas(tar1, tar2, ponto1, ponto2)
    tar_filho2 = pmx_tarefas(tar2, tar1, ponto1, ponto2)

    # Filho 1 herda posições do parent2, filho 2 herda posições do parent1
    def montar(posicoes, tarefas):
        m = [['' for _ in range(dimensao)] for _ in range(dimensao)]
        pos_embaralhadas = posicoes[:]
        random.shuffle(pos_embaralhadas)  # embaralha posições para mais diversidade
        for idx, tarefa in enumerate(tarefas):
            if idx < len(pos_embaralhadas):
                i, j = pos_embaralhadas[idx]
                m[i][j] = tarefa
        return m

    return montar(pos2, tar_filho1), montar(pos1, tar_filho2)


def mutate(mapping, dimensao, mutation_rate=0.3):
    m = [row[:] for row in mapping]
    if random.random() < mutation_rate:
        todas = [(i, j) for i in range(dimensao) for j in range(dimensao)]
        preenchidas = [(i, j) for i, j in todas if m[i][j] != '']
        vazias = [(i, j) for i, j in todas if m[i][j] == '']

        tipo = random.random()
        if tipo < 0.4 and len(preenchidas) >= 2:
            # Troca duas tarefas entre si
            (i1, j1), (i2, j2) = random.sample(preenchidas, 2)
            m[i1][j1], m[i2][j2] = m[i2][j2], m[i1][j1]
        elif tipo < 0.7 and vazias and preenchidas:
            # Move tarefa para célula vazia
            (i1, j1) = random.choice(preenchidas)
            (i2, j2) = random.choice(vazias)
            m[i2][j2] = m[i1][j1]
            m[i1][j1] = ''
        elif preenchidas:
            # Reorganiza todas as posições aleatoriamente
            tarefas = [m[i][j] for i, j in preenchidas]
            random.shuffle(tarefas)
            for idx, (i, j) in enumerate(preenchidas):
                m[i][j] = tarefas[idx]
    return m


# ─────────────────────────────────────────────────────────────
# Algoritmo principal
# ─────────────────────────────────────────────────────────────

def Run_NSGA2(matrix, dimensao, roteamento, pop_size=150, generations=160,
              selecao=[True, True, True], plotar_pareto=True):

    num_objetivos = sum(selecao)
    if num_objetivos < 2:
        raise ValueError("NSGA-II requer pelo menos 2 objetivos selecionados.")

    num_tarefas = len(matrix)

    population = [
        Individuo(generate_random_mapping(dimensao, num_tarefas),
                  matrix, dimensao, roteamento, selecao)
        for _ in range(pop_size)
    ]

    objetivos_unicos = set(tuple(ind.objetivos) for ind in population)
    print(f"Geração 0: {len(objetivos_unicos)} objetivos únicos de {pop_size} indivíduos")

    for gen in range(generations):
        offspring = []
        while len(offspring) < pop_size:
            p1 = _torneio(population)
            p2 = _torneio(population)
            c1_map, c2_map = crossover(p1.mapeamento, p2.mapeamento, dimensao)
            c1_map = mutate(c1_map, dimensao)
            c2_map = mutate(c2_map, dimensao)
            offspring.append(Individuo(c1_map, matrix, dimensao, roteamento, selecao))
            if len(offspring) < pop_size:
                offspring.append(Individuo(c2_map, matrix, dimensao, roteamento, selecao))

        combined = population + offspring
        fronts = fast_non_dominated_sort(combined)

        objetivos_unicos = set(tuple(ind.objetivos) for ind in combined)
        mapeamentos_unicos = set(
            tuple(ind.mapeamento[r][c]
                  for r in range(dimensao) for c in range(dimensao))
            for ind in combined
        )
        print(f"Geração {gen+1}: {len(objetivos_unicos)} obj únicos | "
              f"{len(mapeamentos_unicos)} mapeamentos únicos | "
              f"frente Pareto: {len(fronts[0])}")

        new_population = []
        i = 0
        while i < len(fronts) and len(new_population) + len(fronts[i]) <= pop_size:
            calculate_crowding_distance(fronts[i])
            new_population.extend(fronts[i])
            i += 1
        if len(new_population) < pop_size and i < len(fronts):
            calculate_crowding_distance(fronts[i])
            fronts[i].sort(key=lambda x: (-x.crowding_distance, x.rank))
            new_population.extend(fronts[i][:pop_size - len(new_population)])

        population = new_population

    fronts = fast_non_dominated_sort(population)
    pareto_front = fronts[0]

    print(f"\n=== Frente de Pareto ({len(pareto_front)} indivíduos) ===")
    for i, ind in enumerate(pareto_front):
        print(f"\nIndivíduo {i+1}:")
        for linha in ind.mapeamento:
            print("  ", linha)
        print(f"  Objetivos: {ind.objetivos}")

    if plotar_pareto:
        plotar_frente_pareto(pareto_front, selecao)

    calculate_crowding_distance(pareto_front)
    best = max(pareto_front, key=lambda x: x.crowding_distance)
    return best.mapeamento

def _torneio(population, k=2):
    """Seleção por torneio binário."""
    candidatos = random.sample(population, k)
    return min(candidatos, key=lambda x: (x.rank, -x.crowding_distance))


_NOMES_OBJ = ["Energia", "Latência", "Tolerância"]
_LABELS_OBJ = ["Energia (bandwidth × hops)", "Latência (max hop × bw)", "Tolerância (−vizinhos)"]


def plotar_frente_pareto(pareto_front, selecao):
    """
    Plota a frente de Pareto.
    - 2 objetivos → scatter 2D
    - 3 objetivos → scatter 3D
    Cada ponto é um mapeamento não-dominado.
    """
    if not pareto_front:
        print("Frente de Pareto vazia — nada a plotar.")
        return

    # Montar lista de labels dos objetivos ativos
    labels_ativos = [_LABELS_OBJ[i] for i, s in enumerate(selecao) if s]
    n_obj = len(labels_ativos)

    # Extrair coordenadas — inverte sinal de tolerância para mostrar valor real
    coords = []
    for ind in pareto_front:
        ponto = []
        obj_idx = 0
        for i, s in enumerate(selecao):
            if s:
                v = ind.objetivos[obj_idx]
                if i == 2:   # tolerância foi negada para minimizar
                    v = -v
                ponto.append(v)
                obj_idx += 1
        coords.append(ponto)

    xs = [p[0] for p in coords]
    ys = [p[1] for p in coords]

    # Cor dos pontos proporcional ao crowding distance (diversidade)
    cd_vals = [ind.crowding_distance for ind in pareto_front]
    cd_finito = [v for v in cd_vals if v != float('inf')]
    cd_max = max(cd_finito) if cd_finito else None
    # Se cd_max é None ou 0, todos os pontos recebem a mesma cor
    if cd_max:
        cores = [min(v, cd_max) / cd_max for v in cd_vals]
    else:
        cores = [1.0] * len(cd_vals)

    fig = plt.figure(figsize=(8, 6))
    fig.patch.set_facecolor('#FAFAFA')

    if n_obj == 3:
        zs = [p[2] for p in coords]
        ax = fig.add_subplot(111, projection='3d')
        ax.set_facecolor('#FAFAFA')
        sc = ax.scatter(xs, ys, zs, c=cores, cmap='plasma', s=80, edgecolors='#333', linewidths=0.5, alpha=0.9)
        ax.set_xlabel(labels_ativos[0], fontsize=9, labelpad=8)
        ax.set_ylabel(labels_ativos[1], fontsize=9, labelpad=8)
        ax.set_zlabel(labels_ativos[2], fontsize=9, labelpad=8)
        ax.set_title("Frente de Pareto — NSGA-II", fontsize=13, fontweight='bold', pad=14)
    else:
        ax = fig.add_subplot(111)
        ax.set_facecolor('#F5F5F5')
        sc = ax.scatter(xs, ys, c=cores, cmap='plasma', s=90,
                        edgecolors='#333', linewidths=0.5, alpha=0.9, zorder=3)

        # Linha conectando os pontos da frente (ordena pelo eixo X)
        pares = sorted(zip(xs, ys))
        ax.plot([p[0] for p in pares], [p[1] for p in pares],
                color='#AAAAAA', linewidth=1, linestyle='--', zorder=2)

        ax.set_xlabel(labels_ativos[0], fontsize=10)
        ax.set_ylabel(labels_ativos[1], fontsize=10)
        ax.set_title("Frente de Pareto — NSGA-II", fontsize=13, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.4)

    cbar = fig.colorbar(sc, ax=ax, pad=0.02, fraction=0.03)
    cbar.set_label("Crowding distance (diversidade)", fontsize=8)

    plt.tight_layout()
    plt.savefig("pareto_front.png", dpi=120, bbox_inches='tight')
    plt.show()

"""
import random

# 16 tarefas numa grade 5x5 (25 células, 9 vazias) — força trade-offs reais
n = 16
matrix_adj = [[0]*n for _ in range(n)]

# Comunicações assimétricas e densas com pesos variados
comunicacoes = [
    (0,1,850), (0,2,120), (0,4,430), (0,7,90),
    (1,2,2300),(1,3,670), (1,5,180), (1,8,340),
    (2,3,980), (2,4,7800),(2,6,230), (2,9,560),
    (3,5,3400),(3,6,780), (3,7,120), (3,10,450),
    (4,5,290), (4,6,1200),(4,8,670), (4,11,890),
    (5,6,4500),(5,7,340), (5,9,780), (5,12,230),
    (6,7,1800),(6,8,560), (6,10,340),(6,13,670),
    (7,8,290), (7,9,2100),(7,11,450),(7,14,120),
    (8,9,3200),(8,10,670),(8,12,890),(8,15,560),
    (9,10,450),(9,11,1800),(9,13,340),
    (10,11,2700),(10,12,560),(10,14,780),
    (11,12,890),(11,13,4200),(11,15,230),
    (12,13,670),(12,14,340),(12,15,1200),
    (13,14,3800),(13,15,560),
    (14,15,2100),
    # comunicações de volta (assimétricas)
    (1,0,320), (2,1,890), (3,2,450), (4,3,670),
    (5,4,120), (6,5,1800),(7,6,560), (8,7,340),
    (9,8,780), (10,9,230),(11,10,890),(12,11,450),
    (13,12,1200),(14,13,670),(15,14,340),
    # conexões longas que conflitam com energia
    (0,15,2300),(1,14,1800),(2,13,3400),(3,12,890),
    (4,11,2100),(5,10,1500),(6,9,780), (7,8,340),
]

for i, j, bw in comunicacoes:
    matrix_adj[i][j] = bw

melhor = Run_NSGA2(
    matrix=matrix_adj,
    dimensao=5,
    roteamento="XY",
    pop_size=150,
    generations=150,
    selecao=[True, True, True],
    plotar_pareto=True
)

print("\n=== Melhor Mapeamento ===")
for linha in melhor:
    print(linha)
"""
