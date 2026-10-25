#include <vector>

// Looks for the second value only after the position of the maximum.
int second_largest(const std::vector<int>& a) {
    std::size_t m = 0;
    for (std::size_t i = 1; i < a.size(); ++i) if (a[i] > a[m]) m = i;
    int answer = -1;
    for (std::size_t i = m + 1; i < a.size(); ++i) if (a[i] < a[m] && a[i] > answer) answer = a[i];
    return answer;
}
