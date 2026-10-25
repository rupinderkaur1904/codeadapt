#include <vector>

std::vector<int> plus_one(const std::vector<int>& digits) {
    std::vector<int> out(digits);
    int carry = 1;
    for (std::size_t k = out.size(); k-- > 0 && carry;) {
        const int s = out[k] + carry;
        out[k] = s % 10;
        carry = s / 10;
    }
    if (carry) out.insert(out.begin(), 1);
    return out;
}
