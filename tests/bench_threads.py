import subprocess
import os
import re
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

NUM1 = "1" + "2345678901" * 2000  # ~20001 dígitos
NUM2 = "9" + "8765432109" * 2000  # ~20001 dígitos

DEPTHS     = [0, 1, 2, 3, 4, 5, 6, 8, 10, 16]
REPETICOES = 5

def compilar(depth):
    with open("../CUDA_X_Threads/karatsuba_threads.cpp", "r") as f:
        src = f.read()
    src_mod = re.sub(r"const int MAX_DEPTH = \d+;",
                     f"const int MAX_DEPTH = {depth};", src)
    with open("_tmp_threads.cpp", "w") as f:
        f.write(src_mod)
    subprocess.run(["g++", "-O2", "-pthread", "-o", "_tmp_threads",
                    "_tmp_threads.cpp"], check=True)
    os.remove("_tmp_threads.cpp")

def medir():
    entrada  = f"{NUM1}\n{NUM2}\n"
    resultado = subprocess.run(["./_tmp_threads"], input=entrada,
                               capture_output=True, text=True, check=True)
    match = re.search(r"Tempo:\s+([\d.]+)\s+ms", resultado.stdout)
    return float(match.group(1)) if match else None

def benchmark():
    resultados = []
    print(f"{'DEPTH':>6} | {'Threads':>10} | {'Tempo médio (ms)':>18}")
    print("=" * 45)
    for d in DEPTHS:
        compilar(d)
        tempos = [medir() for _ in range(REPETICOES)]
        media  = sum(x for x in tempos if x is not None) / len(tempos)
        threads = 1 << d
        resultados.append((d, threads, media))
        print(f"{d:>6} | {threads:>10,} | {media:>18.3f}")
    return resultados

def plotar(resultados):
    depths  = [r[0] for r in resultados]
    tempos  = [r[2] for r in resultados]
    threads = [r[1] for r in resultados]

    fig, ax = plt.subplots(figsize=(11, 6))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#1a1d27")
    ax.tick_params(colors="#cccccc")
    ax.xaxis.label.set_color("#cccccc")
    ax.yaxis.label.set_color("#cccccc")
    ax.title.set_color("#ffffff")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333344")

    ax.plot(depths, tempos, "o-", color="#4fc3f7", linewidth=2, markersize=8)
    for d, t, n in zip(depths, tempos, threads):
        ax.annotate(f"{n}t", (d, t), textcoords="offset points",
                    xytext=(0, 10), ha="center", color="#888899", fontsize=9)

    melhor = min(resultados, key=lambda r: r[2])
    ax.axvline(x=melhor[0], color="#66bb6a", linestyle="--", linewidth=1.5,
               label=f"Melhor: depth={melhor[0]} ({melhor[1]} threads)")

    ax.set_title("Impacto do MAX_DEPTH no Karatsuba paralelo (CPU)",
                 fontsize=13, pad=12)
    ax.set_xlabel("MAX_DEPTH", fontsize=11)
    ax.set_ylabel("Tempo médio (ms)", fontsize=11)
    ax.legend(facecolor="#1a1d27", edgecolor="#333344",
              labelcolor="#cccccc", fontsize=10)
    ax.grid(True, color="#2a2d3a", linestyle="--", linewidth=0.7)
    plt.tight_layout()
    plt.savefig("../results/bench_max_depth.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.show()

if __name__ == "__main__":
    resultados = benchmark()
    plotar(resultados)