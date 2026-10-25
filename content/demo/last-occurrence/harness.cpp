// Private test harness for `last-occurrence`. Reads one test case from stdin, calls the
// student's function once and prints the returned index.
//
// Input: <mode> ... <target>
//   L n a_1 .. a_n target    literal array
//   A n start step target    arithmetic progression start, start+step, ...
//   D n value target         n copies of value
#include <cstdio>
#include <iostream>
#include <vector>

int last_occurrence(const std::vector<int>& a, int target);

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
        for (long long i = 0; i < n; ++i) a.push_back(static_cast<int>(start + i * step));
    } else if (mode == 'D') {
        int v; std::cin >> v;
        a.assign(static_cast<std::size_t>(n), v);
    } else {
        return 64;
    }
    int target;
    if (!(std::cin >> target)) return 64;
    const int result = last_occurrence(a, target);
    std::printf("%d\n", result);
    return 0;
}
