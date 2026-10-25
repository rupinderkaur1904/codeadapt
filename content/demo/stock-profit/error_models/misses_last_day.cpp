#include <algorithm>
#include <vector>

// Error model: the loop stops one day early, so selling on the last day is never considered.
int max_profit(const std::vector<int>& prices) {
    int cheapest = prices[0], best = 0;
    for (std::size_t i = 1; i + 1 < prices.size(); ++i) {
        best = std::max(best, prices[i] - cheapest);
        cheapest = std::min(cheapest, prices[i]);
    }
    return best;
}
