#include <climits>
#include <vector>

int closest_pair_gap(const std::vector<int>& a, int target) {
    int best = INT_MAX;
    for (int left = 1, right = static_cast<int>(a.size()) - 1; left < right;) {
        const int s = a[left] + a[right];
        const int g = s > target ? s - target : target - s;
        if (g < best) best = g;
        if (s == target) break;
        if (s < target) ++left; else --right;
    }
    return best;
}
