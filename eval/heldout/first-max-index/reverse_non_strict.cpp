#include <vector>

// Scans from the end; >= moves the answer towards the front on ties.
int first_max_index(const std::vector<int>& a) {
    int pos = static_cast<int>(a.size()) - 1;
    for (int i = pos; i >= 0; --i) {
        if (a[i] >= a[pos]) pos = i;
    }
    return pos;
}
