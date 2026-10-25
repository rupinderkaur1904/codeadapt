#include <algorithm>
#include <climits>
#include <vector>

// Error model: insists on one transaction, so a falling market returns a negative profit (and a
// single day returns INT_MIN) instead of 0.
int max_profit(const std::vector<int>& prices) {
    int cheapest = prices[0], best = INT_MIN;
    for (std::size_t i = 1; i < prices.size(); ++i) {
        best = std::max(best, prices[i] - cheapest);
        cheapest = std::min(cheapest, prices[i]);
    }
    return best;
}
