#include <vector>

// Add from the least significant digit; a carry out of the top digit adds a new leading 1.
std::vector<int> plus_one(const std::vector<int>& digits) {
    std::vector<int> r(digits);
    for (int i = static_cast<int>(r.size()) - 1; i >= 0; --i) {
        if (r[i] < 9) {
            ++r[i];
            return r;
        }
        r[i] = 0;
    }
    r.insert(r.begin(), 1);
    return r;
}
