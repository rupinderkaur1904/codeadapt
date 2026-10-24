#include <vector>

static int days_for(const std::vector<int>& w, int cap) {
    int days = 0;
    std::size_t i = 0;
    while (i < w.size()) {
        int load = 0;
        while (i < w.size() && load + w[i] <= cap) load += w[i++];
        ++days;
    }
    return days;
}

// Counting-style search (step halving) over capacities from the heaviest package upward.
int min_capacity(const std::vector<int>& weights, int days) {
    int heaviest = 0, total = 0;
    for (int x : weights) { if (x > heaviest) heaviest = x; total += x; }
    int first = heaviest, count = total - heaviest;
    while (count > 0) {
        int step = count / 2;
        if (days_for(weights, first + step) > days) {
            first += step + 1;
            count -= step + 1;
        } else {
            count = step;
        }
    }
    return first;
}
