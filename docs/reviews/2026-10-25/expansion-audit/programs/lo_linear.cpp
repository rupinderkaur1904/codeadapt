#include <vector>
int last_occurrence(const std::vector<int>& a, int t) { for (int i = (int)a.size() - 1; i >= 0; --i) if (a[i] == t) return i; return -1; }
