#include <algorithm>
#include <vector>

std::vector<int> plus_one(const std::vector<int>& digits) {
    std::vector<int> rev(digits.rbegin(), digits.rend());
    std::size_t i = 0;
    while (i < rev.size() && rev[i] == 9) rev[i++] = 0;
    if (i == rev.size()) rev.push_back(1);
    else ++rev[i];
    std::reverse(rev.begin(), rev.end());
    return rev;
}
