// Private test harness for `dedup-sorted`. Reads one test case from stdin, calls the student's
// function once and prints the returned length and the kept prefix.
//
// Input: <mode> n ...
//   L n a_1 .. a_n     literal sorted array
//   B n block          a_i = i / block, for i = 0 .. n-1 (runs of equal values)
// Constraints (checked): 1 <= n <= 100000, -1000000000 <= a_i <= 1000000000, sorted
// non-decreasing.
// Output: "k" followed by a[0..k-1] when k <= 40; otherwise "k first last hash" with a fixed
// polynomial hash of the prefix. A k outside [0, n] is printed as "k=<k> invalid".
#include <cstdint>
#include <cstdio>
#include <iostream>
#include <vector>

int remove_duplicates(std::vector<int>& a);

int main() {
    char mode = 0;
    long long n = 0;
    if (!(std::cin >> mode >> n) || n < 1 || n > 100000) return 64;
    std::vector<long long> v;
    v.reserve(static_cast<std::size_t>(n));
    if (mode == 'L') {
        for (long long i = 0; i < n; ++i) { long long x; if (!(std::cin >> x)) return 64; v.push_back(x); }
    } else if (mode == 'B') {
        long long block;
        if (!(std::cin >> block) || block < 1) return 64;
        for (long long i = 0; i < n; ++i) v.push_back(i / block);
    } else {
        return 64;
    }
    std::vector<int> a;
    a.reserve(v.size());
    for (std::size_t i = 0; i < v.size(); ++i) {
        if (v[i] < -1000000000LL || v[i] > 1000000000LL) return 64;
        if (i > 0 && v[i] < v[i - 1]) return 64;
        a.push_back(static_cast<int>(v[i]));
    }
    const int k = remove_duplicates(a);
    if (k < 0 || static_cast<std::size_t>(k) > a.size()) {
        std::printf("k=%d invalid\n", k);
        return 0;
    }
    if (k <= 40) {
        std::printf("%d", k);
        for (int i = 0; i < k; ++i) std::printf(" %d", a[i]);
        std::printf("\n");
    } else {
        std::uint64_t h = 1469598103934665603ULL;
        for (int i = 0; i < k; ++i)
            h = h * 1000003ULL + static_cast<std::uint64_t>(static_cast<std::int64_t>(a[i]) + 2000000000LL);
        std::printf("%d %d %d %llu\n", k, a[0], a[k - 1], static_cast<unsigned long long>(h));
    }
    return 0;
}
