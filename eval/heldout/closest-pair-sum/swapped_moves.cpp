#include <climits>
#include <vector>

int closest_pair_gap(const std::vector<int>& a, int target) {
    int left = 0, right = static_cast<int>(a.size()) - 1, best = INT_MAX;
    while (left < right) {
        const int s = a[left] + a[right];
        const int g = s > target ? s - target : target - s;
        if (g < best) best = g;
        if (s == target) break;
        if (s > target) left++; else right--;
    }
    return best;
}
