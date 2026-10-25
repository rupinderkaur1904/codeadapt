// Private test harness for `pivot-index`. Reads one test case from stdin, calls the
// student's function once and prints the returned index.
//
// Input: <mode> n ...
//   L n a_1 .. a_n             literal array
//   R n mult add mod base      a_i = (i * mult + add) % mod + base, for i = 0 .. n-1
// Constraints (checked): 1 <= n <= 100000, -10000 <= a_i <= 10000.
#include <cstdio>
#include <iostream>
#include <vector>

int pivot_index(const std::vector<int>& a);

int main() {
    char mode = 0;
    long long n = 0;
    if (!(std::cin >> mode >> n) || n < 1 || n > 100000) return 64;
    std::vector<long long> v;
    v.reserve(static_cast<std::size_t>(n));
    if (mode == 'L') {
        for (long long i = 0; i < n; ++i) { long long x; if (!(std::cin >> x)) return 64; v.push_back(x); }
    } else if (mode == 'R') {
        long long mult, add, mod, base;
        if (!(std::cin >> mult >> add >> mod >> base) || mult < 0 || add < 0 || mod < 1) return 64;
        for (long long i = 0; i < n; ++i) v.push_back((i * mult + add) % mod + base);
    } else {
        return 64;
    }
    std::vector<int> a;
    a.reserve(v.size());
    for (long long x : v) {
        if (x < -10000 || x > 10000) return 64;
        a.push_back(static_cast<int>(x));
    }
    const int result = pivot_index(a);
    std::printf("%d\n", result);
    return 0;
}
