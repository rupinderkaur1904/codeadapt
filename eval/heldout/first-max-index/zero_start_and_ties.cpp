#include <vector>

// Two errors at once: starts the maximum at 0 and replaces it on ties.
int first_max_index(const std::vector<int>& a) {
    int top = 0, pos = 0;
    for (int i = 0; i < static_cast<int>(a.size()); ++i) {
        if (a[i] >= top) {
            top = a[i];
            pos = i;
        }
    }
    return pos;
}
