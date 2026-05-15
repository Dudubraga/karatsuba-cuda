#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <thread>
using namespace std;

using BigNum = vector<int>;

const int MAX_DEPTH = 4;

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

// remove zeros à esquerda
void trim(BigNum& n){
    while(n.size() > 1 && n.back() == 0){
        n.pop_back();
    }
}

BigNum add(const BigNum& a, const BigNum& b){
    BigNum result;
    int carry = 0;
    int n = max(a.size(), b.size());
    for(int i = 0; i < n || carry; i++){
        int sum = carry;
        if(i < (int)a.size()) sum += a[i];
        if(i < (int)b.size()) sum += b[i];
        result.push_back(sum % 10);
        carry = sum / 10;
    }
    return result;
}

BigNum subtract(const BigNum& a, const BigNum& b){
    BigNum result;
    int borrow = 0;
    for(int i = 0; i < (int)a.size(); i++){
        int diff = a[i] - borrow;
        if(i < (int)b.size()) diff -= b[i];
        if(diff < 0){ diff += 10; borrow = 1; }
        else borrow = 0;
        result.push_back(diff);
    }
    trim(result);
    return result;
}

// pow(n * 10^shift)
BigNum shiftLeft(const BigNum& n, int shift){
    if(n.size() == 1 && n[0] == 0){ return {0}; }
    BigNum result(shift, 0);
    result.insert(result.end(), n.begin(), n.end());
    return result;
}

BigNum karatsuba(const BigNum& x, const BigNum& y, int depth = 0){
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

    BigNum z0, z1, z2;

    if(depth < MAX_DEPTH){
        thread t0([&]{ z0 = karatsuba(b, d, depth + 1); });
        thread t2([&]{ z2 = karatsuba(a, c, depth + 1); });
        z1 = karatsuba(add(a, b), add(c, d), depth + 1);
        t0.join();
        t2.join();
    }else{
        z0 = karatsuba(b, d, depth + 1);
        z2 = karatsuba(a, c, depth + 1);
        z1 = karatsuba(add(a, b), add(c, d), depth + 1);
    }

    z1 = subtract(z1, z2);
    z1 = subtract(z1, z0);

    BigNum result = add(add(shiftLeft(z2, 2 * half), shiftLeft(z1, half)), z0);
    trim(result);
    return result;
}

int main(){
    string s1, s2;
    cout << "\n=== Karatsuba (CPU Threads) ===\n\n";
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