#include <algorithm>
#include <vector>

// Alternative (unmodelled) error: returns the smallest distinct value instead of the second largest.
int second_largest(const std::vector<int>& a) {
    std::vector<int> b(a);
    std::sort(b.begin(), b.end());
    b.erase(std::unique(b.begin(), b.end()), b.end());
    return b.size() < 2 ? -1 : b[0];
}
