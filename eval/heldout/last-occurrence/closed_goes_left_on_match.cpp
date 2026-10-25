#include <vector>

// Closed-interval search that records a match and keeps looking to the left.
int last_occurrence(const std::vector<int>& a, int target) {
    int left = 0, right = static_cast<int>(a.size()) - 1, answer = -1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (a[mid] >= target) {
            if (a[mid] == target) answer = mid;
            right = mid - 1;
        } else {
            left = mid + 1;
        }
    }
    return answer;
}
