// Private test harness for `integer-sqrt`. Reads one integer x from stdin, calls the
// student's function once and prints the result.
//
// Input: x    with 0 <= x <= 2^31 - 1
#include <cstdio>
#include <iostream>

int int_sqrt(int x);

int main() {
    long long x = -1;
    if (!(std::cin >> x) || x < 0 || x > 2147483647LL) return 64;
    const int result = int_sqrt(static_cast<int>(x));
    std::printf("%d\n", result);
    return 0;
}
