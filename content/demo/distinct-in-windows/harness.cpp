// Private test harness for `distinct-in-windows`. Reads one test case from stdin, calls the
// student's function once and prints the returned counts.
//
// Input: <mode> n ... k
//   L n a_1 .. a_n k            literal array
//   R n mult add mod base k     a_i = (i * mult + add) % mod + base, for i = 0 .. n-1
// Constraints (checked): 1 <= k <= n <= 100000, 0 <= a_i <= 1000000000.
// Output: the counts separated by spaces when there are at most 40; otherwise
// "len=<size> first=<c> last=<c> hash=<h>" with a fixed polynomial hash.
#include <cstdint>
#include <cstdio>
#include <iostream>
#include <vector>

std::vector<int> distinct_in_windows(const std::vector<int>& a, int k);

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
    long long k;
    if (!(std::cin >> k) || k < 1 || k > n) return 64;
    std::vector<int> a;
    a.reserve(v.size());
    for (long long x : v) {
        if (x < 0 || x > 1000000000LL) return 64;
        a.push_back(static_cast<int>(x));
    }
    const std::vector<int> r = distinct_in_windows(a, static_cast<int>(k));
    if (r.empty()) {
        std::printf("empty\n");
    } else if (r.size() <= 40) {
        for (std::size_t i = 0; i < r.size(); ++i) std::printf(i ? " %d" : "%d", r[i]);
        std::printf("\n");
    } else {
        std::uint64_t h = 1469598103934665603ULL;
        for (int x : r) h = h * 1000003ULL + static_cast<std::uint64_t>(static_cast<std::int64_t>(x) + 1000);
        std::printf("len=%zu first=%d last=%d hash=%llu\n", r.size(), r.front(), r.back(),
                    static_cast<unsigned long long>(h));
    }
    return 0;
}
