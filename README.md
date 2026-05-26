# Karatsuba CUDA
> Projeto da disciplina de Programação Paralela e Distribuída

## Visão Geral
Implementação do algoritmo de Karatsuba para multiplicação de grandes números inteiros,
com comparativo de desempenho entre CPU sequencial e GPU (CUDA).

## Estrutura do Projeto

| Pasta | Descrição |
|---|---|
| `karatsuba/` | Implementação base do algoritmo de Karatsuba em C++ sequencial (CPU) |
| `CUDA_X_Threads/` | Implementações paralelas: versão com threads (CPU) e versão com CUDA (GPU) |
| `tests/` | Scripts Python para execução dos benchmarks e coleta de métricas |
| `results/` | Gráficos e tabelas gerados pelos benchmarks comparativos |

## Tecnologias
- C++ / CUDA
- Python (benchmarks e gráficos)
- NVIDIA RTX 4050 Laptop GPU

## Integrantes
- [Eduardo Costa Braga](https://github.com/Dudubraga)
- [Henrique Franca Alves de Lima](https://github.com/HenriqueFrancaa)
- [Isabela Medeiros Belo Lopes](https://github.com/belamedeirosbl)
- [Júlia Vilela Cintra Galvão](https://github.com/juliaavilelaa)