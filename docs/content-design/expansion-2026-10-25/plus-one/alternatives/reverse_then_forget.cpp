#include <algorithm>
#include <vector>

// Alternative cause for adds_at_front: reverses the digits, adds correctly, forgets to reverse back.
std::vector<int> plus_one(const std::vector<int>& digits) {
    std::vector<int> r(digits);
    std::reverse(r.begin(), r.end());
    for (std::size_t i = 0; i < r.size(); ++i) {
        if (r[i] < 9) { ++r[i]; return r; }
        r[i] = 0;
    }
    r.push_back(1);
    return r;
}
