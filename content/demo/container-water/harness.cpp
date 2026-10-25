// Private test harness for `container-water`. Reads one test case from stdin, calls the
// student's function once and prints the returned area.
//
// Input: <mode> n ...
//   L n h_1 .. h_n             literal heights
//   R n mult add mod base      h_i = (i * mult + add) % mod + base, for i = 0 .. n-1
// Constraints (checked): 2 <= n <= 100000, 0 <= h_i <= 10000.
#include <cstdio>
#include <iostream>
#include <vector>

int max_water(const std::vector<int>& height);

int main() {
    char mode = 0;
    long long n = 0;
    if (!(std::cin >> mode >> n) || n < 2 || n > 100000) return 64;
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
    std::vector<int> h;
    h.reserve(v.size());
    for (long long x : v) {
        if (x < 0 || x > 10000) return 64;
        h.push_back(static_cast<int>(x));
    }
    const int result = max_water(h);
    std::printf("%d\n", result);
    return 0;
}
