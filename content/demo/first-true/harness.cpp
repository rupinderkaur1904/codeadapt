// Private test harness for `first-true`. Reads one test case from stdin, calls the
// student's function once and prints the returned index.
//
// Input: <mode> ...
//   L n f_1 .. f_n    literal flags (each 0 or 1)
//   P n k             k zeros followed by n - k ones
#include <cstdio>
#include <iostream>
#include <vector>

int first_true(const std::vector<int>& flags);

int main() {
    char mode = 0;
    long long n = 0;
    if (!(std::cin >> mode >> n) || n < 0) return 64;
    std::vector<int> flags;
    flags.reserve(static_cast<std::size_t>(n));
    if (mode == 'L') {
        for (long long i = 0; i < n; ++i) {
            int x;
            if (!(std::cin >> x) || (x != 0 && x != 1)) return 64;
            flags.push_back(x);
        }
    } else if (mode == 'P') {
        long long k;
        if (!(std::cin >> k) || k < 0 || k > n) return 64;
        for (long long i = 0; i < n; ++i) flags.push_back(i < k ? 0 : 1);
    } else {
        return 64;
    }
    const int result = first_true(flags);
    std::printf("%d\n", result);
    return 0;
}
