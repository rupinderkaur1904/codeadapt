#include <vector>

// Error model: when a new maximum appears, the old maximum is not moved to second place.
int second_largest(const std::vector<int>& a) {
    int first = -1, second = -1;
    for (int x : a) {
        if (x > first) {
            first = x;
        } else if (x < first && x > second) {
            second = x;
        }
    }
    return second;
}
