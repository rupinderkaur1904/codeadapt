#include <algorithm>
#include <functional>
#include <vector>

// Alternative cause for counts_duplicates: sort descending and take the second element.
int second_largest(const std::vector<int>& a) {
    std::vector<int> b(a);
    std::sort(b.begin(), b.end(), std::greater<int>());
    return b.size() < 2 ? -1 : b[1];
}
