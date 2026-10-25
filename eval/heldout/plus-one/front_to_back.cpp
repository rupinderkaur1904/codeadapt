#include <vector>

std::vector<int> plus_one(const std::vector<int>& digits) {
    std::vector<int> out(digits);
    int carry = 1;
    for (std::size_t k = 0; k < out.size() && carry; ++k) {
        const int s = out[k] + carry;
        out[k] = s % 10;
        carry = s / 10;
    }
    if (carry) out.push_back(1);
    return out;
}
