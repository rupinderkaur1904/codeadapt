#include <algorithm>
#include <vector>

// Error model: the overall maximum minus the overall minimum, ignoring that the purchase must
// come before the sale.
int max_profit(const std::vector<int>& prices) {
    const auto [lo, hi] = std::minmax_element(prices.begin(), prices.end());
    return *hi - *lo;
}
