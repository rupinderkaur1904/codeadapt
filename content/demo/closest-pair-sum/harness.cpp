// Private test harness for `closest-pair-sum`. Reads one test case from stdin, calls the
// student's function once and prints the returned gap.
//
// Input: <mode> n ... target
//   L n a_1 .. a_n target      literal sorted array
//   S n step start target      a_i = start + i * step, for i = 0 .. n-1 (step >= 0)
// Constraints (checked): 2 <= n <= 100000, -100000000 <= a_i, target <= 100000000, and the
// array is sorted in non-decreasing order.
#include <cstdio>
#include <iostream>
#include <vector>

int closest_pair_gap(const std::vector<int>& a, int target);

int main() {
    char mode = 0;
    long long n = 0;
    if (!(std::cin >> mode >> n) || n < 2 || n > 100000) return 64;
    std::vector<long long> v;
    v.reserve(static_cast<std::size_t>(n));
    if (mode == 'L') {
        for (long long i = 0; i < n; ++i) { long long x; if (!(std::cin >> x)) return 64; v.push_back(x); }
    } else if (mode == 'S') {
        long long step, start;
        if (!(std::cin >> step >> start) || step < 0) return 64;
        for (long long i = 0; i < n; ++i) v.push_back(start + i * step);
    } else {
        return 64;
    }
    long long target;
    if (!(std::cin >> target) || target < -100000000LL || target > 100000000LL) return 64;
    std::vector<int> a;
    a.reserve(v.size());
    for (std::size_t i = 0; i < v.size(); ++i) {
        if (v[i] < -100000000LL || v[i] > 100000000LL) return 64;
        if (i > 0 && v[i] < v[i - 1]) return 64;
        a.push_back(static_cast<int>(v[i]));
    }
    const int result = closest_pair_gap(a, static_cast<int>(target));
    std::printf("%d\n", result);
    return 0;
}
