#include <vector>

// Held-out variant of upper_bound_confusion, written in a closed-interval style that
// differs from the error model's code: `<=` sends equal elements to the left half.
int lower_bound_index(const std::vector<int>& values, int x) {
    int left = 0, right = static_cast<int>(values.size()) - 1, answer = static_cast<int>(values.size());
    while (left <= right) {
        int middle = (left + right) / 2;
        if (values[middle] <= x) {
            left = middle + 1;
        } else {
            answer = middle;
            right = middle - 1;
        }
    }
    return answer;
}
