#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <cuda_runtime.h>
using namespace std;

using BigNum = vector<int>;

const int THREADS_BLOCK = 256;

// ═══════════════════════════════════════════════════════════════════════
//  KERNELS CUDA
// ═══════════════════════════════════════════════════════════════════════

// soma posição a posição, sem carry
__global__ void add_sum_kernel(const int* a, int aLen,
                               const int* b, int bLen,
                               int* out, int n){
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if(i >= n) return;
    int va = (i < aLen) ? a[i] : 0;
    int vb = (i < bLen) ? b[i] : 0;
    out[i] = va + vb;
}

// para cada posição, calcula generate (carry) e propagate (propagação de carry)
__global__ void add_gp_kernel(const int* sum, int* gen, int* prop, int n){
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if(i >= n){ return; }
    gen[i]  = (sum[i] >= 10) ? 1 : 0;
    prop[i] = (sum[i] == 9 ) ? 1 : 0;
}

// prefix scan paralelo para calcular o carry final
// carry[i+1] = gen[i] OR (prop[i] AND carry[i])
__global__ void scan_step_kernel(int* gen, int* prop, int n, int offset){
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if(i >= n || i < offset){ return; }
    int g = gen [i] | (prop[i] & gen [i - offset]);
    int p = prop[i] & prop[i - offset];
    __syncthreads();
    gen [i] = g;
    prop[i] = p;
}

// aplica os carries calculados
__global__ void add_finalize_kernel(const int* sum, const int* carry,
                                    int* out, int n){
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if(i >= n){ return; }
    int c = (i == 0) ? 0 : carry[i - 1];
    int v = sum[i] + c;
    out[i] = v % 10;
}

// subtração paralela (borrow tratado no host por simplicidade)
__global__ void subtract_kernel(const int* a, int aLen,
                                const int* b, int bLen,
                                int* out, int n){
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if(i >= n){ return; }
    int va = (i < aLen) ? a[i] : 0;
    int vb = (i < bLen) ? b[i] : 0;
    out[i] = va - vb;
}

// desloca dígitos para cima preenchendo com zeros
__global__ void shift_kernel(const int* in, int inLen, int* out, int shift){
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if(i < shift){ 
        out[i] = 0;
    }
    else if(i < inLen + shift){ 
        out[i] = in[i - shift]; 
    }
}

// ═══════════════════════════════════════════════════════════════════════
//  UTILITÁRIOS (CPU)
// ═══════════════════════════════════════════════════════════════════════

BigNum fromString(const string& s){
    BigNum result(s.size());
    for(int i = 0; i < (int)s.size(); i++){
        result[s.size() - 1 - i] = s[i] - '0';
    }
    return result;
}

string toString(const BigNum& n){
    int i = n.size() - 1;
    while(i > 0 && n[i] == 0){ i--; }
    string s;
    for(; i >= 0; i--){
        s += ('0' + n[i]);
    }
    return s;
}

void trim(BigNum& n){
    while(n.size() > 1 && n.back() == 0){
        n.pop_back();
    }
}

// ═══════════════════════════════════════════════════════════════════════
//  OPERAÇÕES GPU (soma, subtração, shift)
// ═══════════════════════════════════════════════════════════════════════

BigNum add(const BigNum& a, const BigNum& b){
    int n = max(a.size(), b.size()) + 1;
    size_t bytes = n * sizeof(int);

    int *d_a, *d_b, *d_sum, *d_gen, *d_prop, *d_out;
    cudaMalloc(&d_a   , a.size() * sizeof(int));
    cudaMalloc(&d_b   , b.size() * sizeof(int));
    cudaMalloc(&d_sum , bytes);
    cudaMalloc(&d_gen , bytes);
    cudaMalloc(&d_prop, bytes);
    cudaMalloc(&d_out , bytes);

    cudaMemcpy(d_a, a.data(), a.size() * sizeof(int), cudaMemcpyHostToDevice);
    cudaMemcpy(d_b, b.data(), b.size() * sizeof(int), cudaMemcpyHostToDevice);

    int blocks = (n + THREADS_BLOCK - 1) / THREADS_BLOCK;

    add_sum_kernel<<<blocks, THREADS_BLOCK>>>(
        d_a, a.size(), d_b, b.size(), d_sum, n);

    add_gp_kernel<<<blocks, THREADS_BLOCK>>>(d_sum, d_gen, d_prop, n);

    for(int offset = 1; offset < n; offset *= 2){
        scan_step_kernel<<<blocks, THREADS_BLOCK>>>(d_gen, d_prop, n, offset);
        cudaDeviceSynchronize();
    }

    add_finalize_kernel<<<blocks, THREADS_BLOCK>>>(d_sum, d_gen, d_out, n);

    BigNum result(n);
    cudaMemcpy(result.data(), d_out, bytes, cudaMemcpyDeviceToHost);

    cudaFree(d_a); cudaFree(d_b); cudaFree(d_sum);
    cudaFree(d_gen); cudaFree(d_prop); cudaFree(d_out);

    if(result.back() == 0) result.pop_back();
    return result;
}

BigNum subtract(const BigNum& a, const BigNum& b){
    int n = a.size();
    size_t bytes = n * sizeof(int);

    int *d_a, *d_b, *d_out;
    cudaMalloc(&d_a  , a.size() * sizeof(int));
    cudaMalloc(&d_b  , b.size() * sizeof(int));
    cudaMalloc(&d_out, bytes);

    cudaMemcpy(d_a, a.data(), a.size() * sizeof(int), cudaMemcpyHostToDevice);
    cudaMemcpy(d_b, b.data(), b.size() * sizeof(int), cudaMemcpyHostToDevice);

    int blocks = (n + THREADS_BLOCK - 1) / THREADS_BLOCK;
    subtract_kernel<<<blocks, THREADS_BLOCK>>>(
        d_a, a.size(), d_b, b.size(), d_out, n);

    BigNum result(n);
    cudaMemcpy(result.data(), d_out, bytes, cudaMemcpyDeviceToHost);

    cudaFree(d_a); cudaFree(d_b); cudaFree(d_out);

    // propaga borrow 
    int borrow = 0;
    for(int i = 0; i < n; i++){
        int v = result[i] - borrow;
        if(v < 0){ v += 10; borrow = 1; }
        else borrow = 0;
        result[i] = v;
    }
    trim(result);
    return result;
}

BigNum shiftLeft(const BigNum& n, int shift){
    if(n.size() == 1 && n[0] == 0){ return {0}; }
    int total = n.size() + shift;
    size_t bytes = total * sizeof(int);

    int *d_in, *d_out;
    cudaMalloc(&d_in , n.size() * sizeof(int));
    cudaMalloc(&d_out, bytes);

    cudaMemcpy(d_in, n.data(), n.size() * sizeof(int), cudaMemcpyHostToDevice);

    int blocks = (total + THREADS_BLOCK - 1) / THREADS_BLOCK;
    shift_kernel<<<blocks, THREADS_BLOCK>>>(d_in, n.size(), d_out, shift);

    BigNum result(total);
    cudaMemcpy(result.data(), d_out, bytes, cudaMemcpyDeviceToHost);

    cudaFree(d_in); cudaFree(d_out);
    return result;
}

// ═══════════════════════════════════════════════════════════════════════
//  KARATSUBA (recursão na CPU)
// ═══════════════════════════════════════════════════════════════════════

BigNum karatsuba(const BigNum& x, const BigNum& y){
    int n = max(x.size(), y.size());
    if(n <= 4){
        BigNum result(x.size() + y.size(), 0);
        for(int i = 0; i < (int)x.size(); i++){
            for(int j = 0; j < (int)y.size(); j++){
                result[i + j] += x[i] * y[j];
                if(result[i + j] >= 10){
                    result[i + j + 1] += result[i + j] / 10;
                    result[i + j] %= 10;
                }
            }
        }
        trim(result);
        return result;
    }

    int half   = n / 2;
    int xSplit = min(half, (int)x.size());
    int ySplit = min(half, (int)y.size());

    BigNum b(x.begin()         , x.begin() + xSplit);
    BigNum a(x.begin() + xSplit, x.end());
    BigNum d(y.begin()         , y.begin() + ySplit);
    BigNum c(y.begin() + ySplit, y.end());

    if(a.empty()){ a = {0}; }
    if(b.empty()){ b = {0}; }
    if(c.empty()){ c = {0}; }
    if(d.empty()){ d = {0}; }

    BigNum z0 = karatsuba(b, d);
    BigNum z2 = karatsuba(a, c);
    BigNum z1 = karatsuba(add(a, b), add(c, d));
    z1 = subtract(z1, z2);
    z1 = subtract(z1, z0);

    BigNum result = add(add(shiftLeft(z2, 2 * half), shiftLeft(z1, half)), z0);
    trim(result);
    return result;
}

// ═══════════════════════════════════════════════════════════════════════
//  MAIN
// ═══════════════════════════════════════════════════════════════════════

int main(){
    string s1, s2;
    cout << "\n=== Karatsuba (CUDA) ===\n\n";
    cout << "Numero 1: "; cin >> s1;
    cout << "Numero 2: "; cin >> s2;

    BigNum x = fromString(s1);
    BigNum y = fromString(s2);
    string result = toString(karatsuba(x, y));

    int width = max({s1.size(), s2.size(), result.size()}) + 2;

    cout << "\n"
         << string(width - s1.size(), ' ') << s1 << "\n"
         << "x" << string(width - s2.size() - 1, ' ') << s2 << "\n"
         << string(width, '-') << "\n"
         << string(width - result.size(), ' ') << result << "\n\n";

    return 0;
}
