#include <vector>

// Recursive search over [l, r); the first call starts at position 1.
static int search(const std::vector<int>& f, int l, int r) {
    if (l >= r) return l;
    int mid = (l + r) / 2;
    if (f[mid]) return search(f, l, mid);
    return search(f, mid + 1, r);
}

int first_true(const std::vector<int>& flags) {
    return search(flags, 1, static_cast<int>(flags.size()));
}
