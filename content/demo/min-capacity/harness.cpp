// Private test harness for `min-capacity`. Reads one test case from stdin, calls the
// student's function once and prints the returned capacity.
//
// Input: <mode> n ... days
//   L n w_1 .. w_n days     literal weights
//   C n w days              n packages of weight w
//   P n period days         w_i = i % period + 1 for i = 0 .. n-1
// Constraints (checked): 1 <= n <= 100000, 1 <= w_i <= 10000, 1 <= days <= n.
#include <cstdio>
#include <iostream>
#include <vector>

int min_capacity(const std::vector<int>& weights, int days);

int main() {
    char mode = 0;
    long long n = 0;
    if (!(std::cin >> mode >> n) || n < 1 || n > 100000) return 64;
    std::vector<int> w;
    w.reserve(static_cast<std::size_t>(n));
    if (mode == 'L') {
        for (long long i = 0; i < n; ++i) { int x; std::cin >> x; w.push_back(x); }
    } else if (mode == 'C') {
        int x; std::cin >> x;
        w.assign(static_cast<std::size_t>(n), x);
    } else if (mode == 'P') {
        long long period; std::cin >> period;
        if (period < 1) return 64;
        for (long long i = 0; i < n; ++i) w.push_back(static_cast<int>(i % period + 1));
    } else {
        return 64;
    }
    for (int x : w) if (x < 1 || x > 10000) return 64;
    long long days;
    if (!(std::cin >> days) || days < 1 || days > n) return 64;
    const int result = min_capacity(w, static_cast<int>(days));
    std::printf("%d\n", result);
    return 0;
}
