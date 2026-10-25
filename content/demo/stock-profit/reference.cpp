#include <algorithm>
#include <vector>

// One pass: the best sale on day i uses the cheapest price strictly before it; 0 if no gain.
int max_profit(const std::vector<int>& prices) {
    int cheapest = prices[0], best = 0;
    for (std::size_t i = 1; i < prices.size(); ++i) {
        best = std::max(best, prices[i] - cheapest);
        cheapest = std::min(cheapest, prices[i]);
    }
    return best;
}
