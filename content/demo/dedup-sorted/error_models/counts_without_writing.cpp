#include <vector>

// Error model: counts the distinct values correctly but never moves them, so the prefix still
// holds the original elements.
int remove_duplicates(std::vector<int>& a) {
    int k = 1;
    for (std::size_t i = 1; i < a.size(); ++i) {
        if (a[i] != a[i - 1]) ++k;
    }
    return k;
}
