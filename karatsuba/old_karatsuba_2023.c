#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>

#define MAX_SIZE 65536 /* 2^16 */
#define MAX_INPUT 32768 /* 2^15 */

typedef unsigned long long ull;
typedef struct{
    char num[MAX_SIZE];
    ull size;
} string;

void PrintS(string str){
    ull i = 0;
    while(str.num[i] == '0'){ i++; }
    if(i == str.size){ 
        printf("0\n"); return;
    }
    for(i; i < str.size; i++){
        printf("%c", str.num[i]);
    } printf("\n");
}

void FixSize(char* str1, char* str2, ull size){
    if(size == 1){ return; }
    int p = 1;
    while(size > pow(2, p)){ p++; }
    ull zeros = pow(2, p);
    string power1;
    string power2;
    memset(power1.num, '\0', sizeof(power1.num));
    memset(power2.num, '\0', sizeof(power2.num));
    memset(power1.num, '0', zeros - strlen(str1));
    memset(power2.num, '0', zeros - strlen(str2));
    strcat(power1.num, str1);
    strcat(power2.num, str2);
    strcpy(str1, power1.num);
    strcpy(str2, power2.num);
}

string Zeros(string str, ull size, int n){
    for(int i = 0; i < size / n ; i++){
        str.num[i+str.size] = '0';
    }
    str.size += size / n;
    return str;
}

string Substring(string str, ull pos){
    string s; memset(s.num, '\0', sizeof(s.num));
    s.size = str.size / 2;
    if(pos == 0){
        for(int i = 0; i < s.size; i++){
            s.num[i] = str.num[i];
        }
    }else{
        for(int i = 0; i < s.size; i++){
            s.num[i] = str.num[i + s.size];
        }
    }
    return s;
}

string Sum(string a, string b){
    if(a.size > b.size){
        FixSize(a.num, b.num, a.size);
        a.size = strlen(a.num);
        b.size = strlen(b.num); 
    }
    else if(a.size < b.size){
        FixSize(a.num, b.num, b.size);
        a.size = strlen(a.num);
        b.size = strlen(b.num); 
    }
    ull carry = 0;
    string r; memset(r.num, '\0', sizeof(r));
    string result; memset(result.num, '\0', sizeof(result));
    for(int i = a.size-1; i >= 0; i--){
        ull sum = (a.num[i] - '0') + (b.num[i] - '0');
        r.num[i] = ((sum + carry) % 10) + '0';
        carry = (sum + carry) / 10;
    }
    if(carry != 0){
        result.num[0] = '1';
        strcat(result.num, r.num);
        result.size = strlen(result.num);
    }else{
        strcpy(result.num, r.num);
        result.size = strlen(result.num);
    }
    return result;
}

string Multiply(string x, string y){
        string product; memset(product.num, '\0', sizeof(product.num));
        int r = (x.num[0] - '0') * (y.num[0] - '0');
        if(r >= 10){
            product.num[0] = r / 10 + '0';
            product.num[1] = r % 10 + '0';
        }else{
            product.num[0] = '0';
            product.num[1] = r + '0';
        }
        product.size = 2;
        return product;
}

string Karatsuba(string x, string y){
    if(x.size == 1){
        string result = Multiply(x, y);
        return result;
    }
    string a, b, c, d;
    a = Substring(x, 0); b = Substring(x, 1);
    c = Substring(y, 0); d = Substring(y, 1);
    string ac = Karatsuba(a, c); 
    string ad = Karatsuba(a, d); 
    string bc = Karatsuba(b, c); 
    string bd = Karatsuba(b, d); 
    
    string adbc = Zeros(Sum(ad, bc), x.size, 2); /* 10^n/2 */ 
    string r1 = Zeros(ac, x.size, 1); /* 10^n */
    string r2 = Sum(r1, adbc); 
    string r3 = Sum(r2, bd);
    return r3;
}

int main(){
    string number1; scanf("%s", number1.num); 
    string number2; scanf("%s", number2.num); 
    number1.size = strlen(number1.num);
    number2.size = strlen(number2.num);
    if(number1.size > MAX_INPUT || number2.size > MAX_INPUT){
        printf("Numero muito grande.\n");
        exit(1);
    }

    printf("number 1 -> %s\n", number1.num);
    printf("number 2 -> %s\n", number2.num);

    if(number1.size > number2.size){
        FixSize(number1.num, number2.num, number1.size);
    }else{
        FixSize(number1.num, number2.num, number2.size);
    }
    number1.size = strlen(number1.num);
    number2.size = strlen(number2.num);

    string result = Karatsuba(number1, number2);
    printf("\n= "); PrintS(result); printf("\n");

    return 0;
}
