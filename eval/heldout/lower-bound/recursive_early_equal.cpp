#include <vector>

namespace {
int search(const std::vector<int>& v, int x, int from, int to) {
    if (from >= to) return from;
    int m = (from + to) / 2;
    if (v[m] == x) return m;  // found it
    return v[m] < x ? search(v, x, m + 1, to) : search(v, x, from, m);
}
}  // namespace

int lower_bound_index(const std::vector<int>& a, int target) {
    return search(a, target, 0, static_cast<int>(a.size()));
}
