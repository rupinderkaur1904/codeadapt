#include <algorithm>
#include <vector>

// Returns the smallest distinct value.
int second_largest(const std::vector<int>& a) {
    std::vector<int> b(a);
    std::sort(b.begin(), b.end());
    b.erase(std::unique(b.begin(), b.end()), b.end());
    return b.size() >= 2 ? b.front() : -1;
}
