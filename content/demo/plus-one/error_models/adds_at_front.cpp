#include <vector>

// Error model: treats digits[0] as the least significant digit, so the carry runs from the
// front; a carry out of the end appends a 1.
std::vector<int> plus_one(const std::vector<int>& digits) {
    std::vector<int> r(digits);
    for (std::size_t i = 0; i < r.size(); ++i) {
        if (r[i] < 9) {
            ++r[i];
            return r;
        }
        r[i] = 0;
    }
    r.push_back(1);
    return r;
}
