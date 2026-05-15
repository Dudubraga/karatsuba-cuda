import subprocess
import os
import re
import time
import matplotlib.pyplot as plt

NUM1 = "1" + "2345678901" * 100000  # ~1.000.001 dígitos
NUM2 = "9" + "8765432109" * 100000  # ~1.000.001 dígitos

THREADS_BLOCKS = [32, 64, 128, 256, 512, 1024]
REPETICOES     = 5

# substitui THREADS_BLOCK no .cu, compila e apaga o temporário
def compilar(tb):
    with open("../cuda/karatsuba_cuda.cu", "r") as f:
        src = f.read()
    src_mod = re.sub(r"const int THREADS_BLOCK = \d+;",
                     f"const int THREADS_BLOCK = {tb};", src)
    with open("_tmp_cuda.cu", "w") as f:
        f.write(src_mod)
    subprocess.run(["nvcc", "-O2", "-o", "_tmp_cuda", "_tmp_cuda.cu"], check=True)
    os.remove("_tmp_cuda.cu")

# roda o executável com NUM1 e NUM2, retorna o tempo em ms
def medir():
    entrada = f"{NUM1}\n{NUM2}\n"
    start   = time.perf_counter()
    subprocess.run(["./_tmp_cuda"], input=entrada,
                   capture_output=True, text=True, check=True)
    return (time.perf_counter() - start) * 1000

# compila e mede cada threads_block, imprime tabela e retorna resultados
def benchmark():
    resultados = []
    print(f"{'THREADS_BLOCK':>14} | {'Tempo médio (ms)':>18}")
    print("=" * 37)
    for tb in THREADS_BLOCKS:
        compilar(tb)
        tempos = [medir() for _ in range(REPETICOES)]
        media  = sum(tempos) / len(tempos)
        resultados.append((tb, media))
        print(f"{tb:>14} | {media:>18.3f}")
    return resultados

# gera e salva o gráfico de tempo por THREADS_BLOCK em ../results/bench_threads_block.png
def plotar(resultados):
    tbs    = [r[0] for r in resultados]
    tempos = [r[1] for r in resultados]

    fig, ax = plt.subplots(figsize=(11, 6))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#1a1d27")
    ax.tick_params(colors="#cccccc")
    ax.xaxis.label.set_color("#cccccc")
    ax.yaxis.label.set_color("#cccccc")
    ax.title.set_color("#ffffff")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333344")

    ax.plot(tbs, tempos, "o-", color="#ff7043", linewidth=2, markersize=8)
    for tb, t in zip(tbs, tempos):
        ax.annotate(f"{t:.1f}ms", (tb, t), textcoords="offset points",
                    xytext=(0, 10), ha="center", color="#888899", fontsize=9)

    melhor = min(resultados, key=lambda r: r[1])
    ax.axvline(x=melhor[0], color="#66bb6a", linestyle="--", linewidth=1.5,
               label=f"Melhor: {melhor[0]} threads/bloco")

    ax.set_xscale("log", base=2)
    ax.set_xticks(tbs)
    ax.set_xticklabels(tbs)
    ax.set_title("Impacto do THREADS_BLOCK no Karatsuba CUDA",
                 fontsize=13, pad=12)
    ax.set_xlabel("Threads por bloco", fontsize=11)
    ax.set_ylabel("Tempo médio (ms)", fontsize=11)
    ax.legend(facecolor="#1a1d27", edgecolor="#333344",
              labelcolor="#cccccc", fontsize=10)
    ax.grid(True, color="#2a2d3a", linestyle="--", linewidth=0.7)
    plt.tight_layout()
    plt.savefig("../results/bench_threads_block.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()

if __name__ == "__main__":
    resultados = benchmark()
    plotar(resultados)