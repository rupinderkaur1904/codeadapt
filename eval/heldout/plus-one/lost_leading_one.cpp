#include <vector>

std::vector<int> plus_one(const std::vector<int>& digits) {
    std::vector<int> out(digits);
    int carry = 1;
    for (int k = static_cast<int>(out.size()) - 1; k >= 0; --k) {
        const int s = out[k] + carry;
        out[k] = s % 10;
        carry = s / 10;
    }
    return out;
}
