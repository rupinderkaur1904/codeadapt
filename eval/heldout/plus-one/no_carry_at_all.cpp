#include <vector>

// Increments the last digit with no carry.
std::vector<int> plus_one(const std::vector<int>& digits) {
    std::vector<int> out(digits);
    ++out.back();
    return out;
}
