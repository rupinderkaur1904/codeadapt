#include <vector>

// Error model: handles a carry into the next digit only once, so a second 9 is left at 10.
std::vector<int> plus_one(const std::vector<int>& digits) {
    std::vector<int> r(digits);
    const int n = static_cast<int>(r.size());
    ++r[n - 1];
    if (r[n - 1] == 10) {
        r[n - 1] = 0;
        if (n >= 2) ++r[n - 2];
        else r.insert(r.begin(), 1);
    }
    return r;
}
