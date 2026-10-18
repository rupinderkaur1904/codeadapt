#include <vector>

// Closed interval with a running answer, initialised to "none found".
int first_true(const std::vector<int>& flags) {
    int left = 0, right = (int)flags.size() - 1;
    int answer = (int)flags.size();
    while (left <= right) {
        int middle = left + (right - left) / 2;
        if (flags[middle] == 1) {
            answer = middle;
            right = middle - 1;
        } else {
            left = middle + 1;
        }
    }
    return answer;
}
