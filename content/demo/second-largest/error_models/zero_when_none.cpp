#include <vector>

// Error model: the second largest starts at 0, so "no second value" is reported as 0, not -1.
int second_largest(const std::vector<int>& a) {
    int first = -1, second = 0;
    for (int x : a) {
        if (x > first) {
            if (first > second) second = first;
            first = x;
        } else if (x < first && x > second) {
            second = x;
        }
    }
    return second;
}
