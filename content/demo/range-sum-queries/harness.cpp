// Private test harness for `range-sum-queries`. Reads one test case from stdin, calls the
// student's function once and prints the returned sums.
//
// Input: <mode> n ... q queries
//   L n a_1 .. a_n q l_1 r_1 .. l_q r_q        literal array and queries
//   G n mult add mod base q                     a_i = (i * mult + add) % mod + base; query j is
//                                               l = (j * 7919) % n, r = l + (j * 104729) % (n - l)
// Constraints (checked): 1 <= n, q <= 100000, -10000 <= a_i <= 10000, 0 <= l <= r < n.
// Output: the sums separated by spaces when there are at most 40; otherwise
// "len=<q> first=<s> last=<s> hash=<h>" with a fixed polynomial hash.
#include <cstdint>
#include <cstdio>
#include <iostream>
#include <utility>
#include <vector>

std::vector<long long> range_sums(const std::vector<int>& a,
                                  const std::vector<std::pair<int, int>>& queries);

int main() {
    char mode = 0;
    long long n = 0;
    if (!(std::cin >> mode >> n) || n < 1 || n > 100000) return 64;
    std::vector<long long> v;
    std::vector<std::pair<int, int>> qs;
    long long q = 0;
    if (mode == 'L') {
        for (long long i = 0; i < n; ++i) { long long x; if (!(std::cin >> x)) return 64; v.push_back(x); }
        if (!(std::cin >> q) || q < 1 || q > 100000) return 64;
        for (long long j = 0; j < q; ++j) {
            long long l, r;
            if (!(std::cin >> l >> r) || l < 0 || r < l || r >= n) return 64;
            qs.emplace_back(static_cast<int>(l), static_cast<int>(r));
        }
    } else if (mode == 'G') {
        long long mult, add, mod, base;
        if (!(std::cin >> mult >> add >> mod >> base >> q) || mult < 0 || add < 0 || mod < 1 || q < 1 || q > 100000) return 64;
        for (long long i = 0; i < n; ++i) v.push_back((i * mult + add) % mod + base);
        for (long long j = 0; j < q; ++j) {
            const long long l = (j * 7919) % n;
            const long long r = l + (j * 104729) % (n - l);
            qs.emplace_back(static_cast<int>(l), static_cast<int>(r));
        }
    } else {
        return 64;
    }
    std::vector<int> a;
    for (long long x : v) {
        if (x < -10000 || x > 10000) return 64;
        a.push_back(static_cast<int>(x));
    }
    const std::vector<long long> r = range_sums(a, qs);
    if (r.empty()) {
        std::printf("empty\n");
    } else if (r.size() <= 40) {
        for (std::size_t i = 0; i < r.size(); ++i) std::printf(i ? " %lld" : "%lld", r[i]);
        std::printf("\n");
    } else {
        std::uint64_t h = 1469598103934665603ULL;
        for (long long x : r) h = h * 1000003ULL + static_cast<std::uint64_t>(x + 2000000000LL);
        std::printf("len=%zu first=%lld last=%lld hash=%llu\n", r.size(), r.front(), r.back(),
                    static_cast<unsigned long long>(h));
    }
    return 0;
}
