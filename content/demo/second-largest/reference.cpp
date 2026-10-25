#include <vector>

// Track the largest and the largest strictly smaller value; -1 means "not seen yet".
int second_largest(const std::vector<int>& a) {
    int first = -1, second = -1;
    for (int x : a) {
        if (x > first) {
            second = first;
            first = x;
        } else if (x < first && x > second) {
            second = x;
        }
    }
    return second;
}
