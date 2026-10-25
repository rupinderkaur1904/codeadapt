// Private test harness for `plus-one`. Reads one test case from stdin, calls the student's
// function once and prints the returned digits.
//
// Input: <mode> n ...
//   L n d_1 .. d_n     literal digits, most significant first
//   N n                n nines
//   P n                digits i % 10 for i = 1 .. n (no leading zero)
// Constraints (checked): 1 <= n <= 100000, 0 <= d_i <= 9, d_1 != 0 unless n == 1.
// Output: the digits separated by spaces when the result has at most 40 digits; otherwise
// "len=<size> first=<d> last=<d> hash=<h>" with a fixed polynomial hash, so long results stay
// small and still compare exactly.
#include <cstdint>
#include <cstdio>
#include <iostream>
#include <vector>

std::vector<int> plus_one(const std::vector<int>& digits);

int main() {
    char mode = 0;
    long long n = 0;
    if (!(std::cin >> mode >> n) || n < 1 || n > 100000) return 64;
    std::vector<int> d;
    d.reserve(static_cast<std::size_t>(n));
    if (mode == 'L') {
        for (long long i = 0; i < n; ++i) { int x; if (!(std::cin >> x)) return 64; d.push_back(x); }
    } else if (mode == 'N') {
        d.assign(static_cast<std::size_t>(n), 9);
    } else if (mode == 'P') {
        for (long long i = 1; i <= n; ++i) d.push_back(static_cast<int>(i % 10));
    } else {
        return 64;
    }
    for (int x : d) if (x < 0 || x > 9) return 64;
    if (d.size() > 1 && d[0] == 0) return 64;
    const std::vector<int> r = plus_one(d);
    if (r.size() <= 40) {
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
