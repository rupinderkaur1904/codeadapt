#include <vector>

// Correct compaction, then returns one too many.
int remove_duplicates(std::vector<int>& a) {
    int w = 1;
    for (std::size_t r = 1; r < a.size(); ++r) if (a[r] != a[w - 1]) a[w++] = a[r];
    return w < static_cast<int>(a.size()) ? w + 1 : w;
}
