#include <vector>

std::vector<int> plus_one(const std::vector<int>& digits) {
    std::vector<int> out(digits);
    out.back() += 1;
    if (out.back() > 9) {
        out.back() -= 10;
        if (out.size() == 1) out.insert(out.begin(), 1);
        else out[out.size() - 2] += 1;
    }
    return out;
}
