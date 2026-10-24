#include <vector>

// Closed-interval search that records each match and keeps looking to the right.
int last_occurrence(const std::vector<int>& a, int target) {
    int left = 0, right = static_cast<int>(a.size()) - 1, answer = -1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (a[mid] == target) {
            answer = mid;
            left = mid + 1;
        } else if (a[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    return answer;
}
