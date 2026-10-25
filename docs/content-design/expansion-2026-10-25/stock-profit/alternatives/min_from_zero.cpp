#include <algorithm>
#include <vector>

// Candidate accumulator error: the cheapest price starts at 0.
int max_profit(const std::vector<int>& prices) {
    int cheapest = 0, best = 0;
    for (std::size_t i = 0; i < prices.size(); ++i) {
        best = std::max(best, prices[i] - cheapest);
        cheapest = std::min(cheapest, prices[i]);
    }
    return best;
}
