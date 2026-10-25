#include <algorithm>
#include <functional>
#include <vector>

int second_largest(const std::vector<int>& a) {
    if (a.size() < 2) return -1;
    std::vector<int> b(a);
    std::sort(b.begin(), b.end(), std::greater<int>());
    return b[1];
}
