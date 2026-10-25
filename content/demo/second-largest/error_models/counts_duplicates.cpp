#include <vector>

// Error model: a value equal to the maximum can become the second largest, so duplicates of
// the maximum are not skipped.
int second_largest(const std::vector<int>& a) {
    int first = -1, second = -1;
    for (int x : a) {
        if (x > first) {
            second = first;
            first = x;
        } else if (x > second) {
            second = x;
        }
    }
    return second;
}
