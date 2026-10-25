#include <climits>
#include <vector>

int closest_pair_gap(const std::vector<int>& a, int target) {
    int left = 0, right = static_cast<int>(a.size()) - 1;
    int best_abs = INT_MAX, answer = 0;
    while (left < right) {
        const int d = a[left] + a[right] - target;
        const int g = d < 0 ? -d : d;
        if (g < best_abs) { best_abs = g; answer = d; }
        if (d == 0) break;
        if (d < 0) ++left; else --right;
    }
    return answer;
}
