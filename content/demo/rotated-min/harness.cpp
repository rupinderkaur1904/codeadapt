// Private test harness for `rotated-min`. Reads one test case from stdin, calls the
// student's function once and prints the returned index.
//
// Input: <mode> n ...
//   L n a_1 .. a_n          literal array
//   R n k start step        b_i = start + i*step (step > 0), rotated so that a[k] = b_0
// Constraints (checked): 1 <= n <= 200000, and the array is a rotation of a strictly
// increasing array.
#include <cstdio>
#include <iostream>
#include <vector>

int rotated_min_index(const std::vector<int>& a);

int main() {
    char mode = 0;
    long long n = 0;
    if (!(std::cin >> mode >> n) || n < 1 || n > 200000) return 64;
    std::vector<int> a;
    a.reserve(static_cast<std::size_t>(n));
    if (mode == 'L') {
        for (long long i = 0; i < n; ++i) { int x; if (!(std::cin >> x)) return 64; a.push_back(x); }
    } else if (mode == 'R') {
        long long k, start, step;
        if (!(std::cin >> k >> start >> step) || k < 0 || k >= n || step <= 0) return 64;
        a.resize(static_cast<std::size_t>(n));
        for (long long j = 0; j < n; ++j) a[j] = static_cast<int>(start + ((j - k + n) % n) * step);
    } else {
        return 64;
    }
    int descents = 0;
    for (std::size_t i = 1; i < a.size(); ++i) {
        if (a[i - 1] == a[i]) return 64;
        if (a[i - 1] > a[i]) ++descents;
    }
    if (descents > 1 || (descents == 1 && a.back() > a.front())) return 64;
    const int result = rotated_min_index(a);
    std::printf("%d\n", result);
    return 0;
}
