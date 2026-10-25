#include <vector>

std::vector<int> plus_one(const std::vector<int>& digits) {
    std::vector<int> out(digits);
    for (int k = static_cast<int>(out.size()) - 1; k >= 0; --k) {
        out[k] = (out[k] + 1) % 10;
    }
    if (out.front() == 0) out.insert(out.begin(), 1);
    return out;
}
