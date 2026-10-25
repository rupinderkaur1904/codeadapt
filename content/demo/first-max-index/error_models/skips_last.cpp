#include <vector>

// Error model: the loop stops one element early, so a maximum in the last position is missed.
int first_max_index(const std::vector<int>& a) {
    int best = 0;
    for (int i = 1; i < static_cast<int>(a.size()) - 1; ++i) {
        if (a[i] > a[best]) best = i;
    }
    return best;
}
