#include <vector>

// Error model: the carry starts at 1 but is never cleared, so 1 is added to every digit.
std::vector<int> plus_one(const std::vector<int>& digits) {
    std::vector<int> r(digits);
    int carry = 1;
    for (int i = static_cast<int>(r.size()) - 1; i >= 0; --i) {
        r[i] += carry;
        if (r[i] == 10) r[i] = 0;
    }
    if (r[0] == 0) r.insert(r.begin(), 1);
    return r;
}
