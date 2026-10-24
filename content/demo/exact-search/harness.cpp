// Private test harness for `exact-search`. Reads one test case from stdin, calls the
// student's function once and prints the returned index.
//
// Input: <mode> ... <target>
//   L n a_1 .. a_n target    literal array (strictly increasing)
//   A n start step target    arithmetic progression start, start+step, ... (step > 0)
#include <cstdio>
#include <iostream>
#include <vector>

int search_index(const std::vector<int>& a, int target);

int main() {
    char mode = 0;
    long long n = 0;
    if (!(std::cin >> mode >> n) || n < 0) return 64;
    std::vector<int> a;
    a.reserve(static_cast<std::size_t>(n));
    if (mode == 'L') {
        for (long long i = 0; i < n; ++i) { int x; std::cin >> x; a.push_back(x); }
    } else if (mode == 'A') {
        long long start, step; std::cin >> start >> step;
        if (step <= 0) return 64;
        for (long long i = 0; i < n; ++i) a.push_back(static_cast<int>(start + i * step));
    } else {
        return 64;
    }
    for (std::size_t i = 1; i < a.size(); ++i) if (a[i - 1] >= a[i]) return 64;
    int target;
    if (!(std::cin >> target)) return 64;
    const int result = search_index(a, target);
    std::printf("%d\n", result);
    return 0;
}
