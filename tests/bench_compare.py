import subprocess
import time
import matplotlib.pyplot as plt

# vários tamanhos para mostrar a curva de speedup
TAMANHOS   = [100, 500, 1000, 5000, 10000, 50000, 100000, 500000]
REPETICOES = 3

VERSOES = {
    "base"    : "../karatsuba/karatsuba_base.exe",
    "threads" : "../CUDA_X_Threads/karatsuba_threads.exe",
    "cuda"    : "../CUDA_X_Threads/karatsuba_cuda.exe",
}

# compila todas as versões
def compilar():
    print("[compilar] g++ base...", flush=True)
    subprocess.run(["g++", "-O2", "-o", "../karatsuba/karatsuba_base.exe",
                    "../karatsuba/karatsuba_base.cpp"], check=True)
    print("[compilar] g++ threads...", flush=True)
    subprocess.run(["g++", "-O2", "-pthread", "-o", "../CUDA_X_Threads/karatsuba_threads.exe",
                    "../CUDA_X_Threads/karatsuba_threads.cpp"], check=True)
    print("[compilar] nvcc cuda...", flush=True)
    vcvars = r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
    cmd = f'"{vcvars}" && nvcc -O2 -o ../CUDA_X_Threads/karatsuba_cuda.exe ../CUDA_X_Threads/karatsuba_cuda.cu'
    subprocess.run(cmd, shell=True, check=True)
    print("[compilar] ok\n", flush=True)

# gera string de N dígitos para testes
def gerar(n):
    return ("12345678901234567890" * (n // 20 + 1))[:n]

# mede o tempo de execução de um executável em ms
def medir(exe, n):
    num1    = gerar(n)
    num2    = gerar(n)
    entrada = f"{num1}\n{num2}\n"
    start   = time.perf_counter()
    subprocess.run([exe], input=entrada, capture_output=True, text=True,
                   check=True, timeout=300)
    return (time.perf_counter() - start) * 1000

# roda cada versão para cada tamanho
def benchmark():
    resultados = {nome: [] for nome in VERSOES}
    linhas = []
    for n in TAMANHOS:
        linha = f"{n:>10,} |"
        for nome, exe in VERSOES.items():
            try:
                tempos = []
                for rep in range(REPETICOES):
                    print(f"  [{nome}] {n:,} dígitos — rep {rep+1}/{REPETICOES}...", flush=True)
                    tempos.append(medir(exe, n))
                media  = sum(tempos) / len(tempos)
                resultados[nome].append(media)
                linha += f" {media:>11.1f}ms |"
            except subprocess.TimeoutExpired:
                print(f"  [{nome}] {n:,} dígitos — TIMEOUT", flush=True)
                resultados[nome].append(None)
                linha += f" {'timeout':>13} |"
        linhas.append(linha)

    header = f"{'Tamanho':>10} | " + " | ".join(f"{v:>12}" for v in VERSOES)
    print("\n" + header)
    print("=" * (12 + len(VERSOES) * 15))
    for l in linhas:
        print(l)
    return resultados

# gera e salva gráfico comparativo
def plotar(resultados):
    cores = {"base": "#4fc3f7", "threads": "#66bb6a", "cuda": "#ff7043"}

    fig, ax = plt.subplots(figsize=(11, 6))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#1a1d27")
    ax.tick_params(colors="#cccccc")
    ax.xaxis.label.set_color("#cccccc")
    ax.yaxis.label.set_color("#cccccc")
    ax.title.set_color("#ffffff")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333344")

    for nome, tempos in resultados.items():
        xs = [TAMANHOS[i] for i, t in enumerate(tempos) if t is not None]
        ys = [t for t in tempos if t is not None]
        ax.plot(xs, ys, "o-", color=cores[nome], label=nome,
                linewidth=2, markersize=7)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_title("Karatsuba — Comparativo das 3 Versões (escala log)",
                 fontsize=13, pad=12)
    ax.set_xlabel("Tamanho do número (dígitos)", fontsize=11)
    ax.set_ylabel("Tempo médio (ms)", fontsize=11)
    ax.legend(facecolor="#1a1d27", edgecolor="#333344",
              labelcolor="#cccccc", fontsize=10)
    ax.grid(True, which="both", color="#2a2d3a", linestyle="--", linewidth=0.7)
    plt.tight_layout()
    plt.savefig("../results/bench_compare.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()

if __name__ == "__main__":
    compilar()
    resultados = benchmark()
    plotar(resultados)