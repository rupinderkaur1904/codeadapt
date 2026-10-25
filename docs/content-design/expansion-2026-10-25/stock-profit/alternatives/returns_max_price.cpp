#include <algorithm>
#include <vector>

// Alternative cause for min_from_zero: misreads the task as "the highest price".
int max_profit(const std::vector<int>& prices) {
    return *std::max_element(prices.begin(), prices.end());
}
