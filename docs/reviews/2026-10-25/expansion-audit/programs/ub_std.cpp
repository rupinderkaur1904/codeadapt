#include <algorithm>
#include <vector>
int upper_bound_index(const std::vector<int>& a, int target) {
    return std::upper_bound(a.begin(), a.end(), target) - a.begin();
}
