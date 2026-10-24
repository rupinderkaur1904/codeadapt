// Private test harness for `peak-index`. Reads one test case from stdin, calls the
// student's function once and prints the returned index.
//
// Input: <mode> n ...
//   L n a_1 .. a_n     literal array
//   M n p              a_i = 2i for i <= p, then a_i = 2p - 3(i - p) for i > p (peak at p)
// Constraints (checked): 1 <= n <= 200000, and the array strictly increases, then strictly
// decreases (either part may be empty).
#include <cstdio>
#include <iostream>
#include <vector>

int peak_index(const std::vector<int>& a);

int main() {
    char mode = 0;
    long long n = 0;
    if (!(std::cin >> mode >> n) || n < 1 || n > 200000) return 64;
    std::vector<int> a;
    a.reserve(static_cast<std::size_t>(n));
    if (mode == 'L') {
        for (long long i = 0; i < n; ++i) { int x; if (!(std::cin >> x)) return 64; a.push_back(x); }
    } else if (mode == 'M') {
        long long p;
        if (!(std::cin >> p) || p < 0 || p >= n) return 64;
        for (long long i = 0; i < n; ++i)
            a.push_back(static_cast<int>(i <= p ? 2 * i : 2 * p - 3 * (i - p)));
    } else {
        return 64;
    }
    std::size_t i = 1;
    while (i < a.size() && a[i - 1] < a[i]) ++i;
    while (i < a.size() && a[i - 1] > a[i]) ++i;
    if (i != a.size()) return 64;
    const int result = peak_index(a);
    std::printf("%d\n", result);
    return 0;
}
