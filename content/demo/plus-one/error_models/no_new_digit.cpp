#include <vector>

// Error model: a carry out of the most significant digit is dropped, so 99 becomes 00.
std::vector<int> plus_one(const std::vector<int>& digits) {
    std::vector<int> r(digits);
    for (int i = static_cast<int>(r.size()) - 1; i >= 0; --i) {
        if (r[i] < 9) {
            ++r[i];
            return r;
        }
        r[i] = 0;
    }
    return r;
}
