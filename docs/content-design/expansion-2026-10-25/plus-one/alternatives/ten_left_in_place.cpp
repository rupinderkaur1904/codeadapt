#include <vector>

// Alternative: increments the last digit without any carry.
std::vector<int> plus_one(const std::vector<int>& digits) {
    std::vector<int> r(digits);
    ++r.back();
    return r;
}
