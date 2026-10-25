#include <vector>

// Error model: the loop starts at index 1 with nothing taken from a[0], so the first element is
// never considered.
int second_largest(const std::vector<int>& a) {
    int first = -1, second = -1;
    for (int i = 1; i < static_cast<int>(a.size()); ++i) {
        const int x = a[i];
        if (x > first) {
            second = first;
            first = x;
        } else if (x < first && x > second) {
            second = x;
        }
    }
    return second;
}
