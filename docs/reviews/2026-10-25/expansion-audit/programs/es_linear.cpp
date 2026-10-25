#include <vector>
int search_index(const std::vector<int>& a, int t) { for (int i = 0; i < (int)a.size(); ++i) if (a[i] == t) return i; return -1; }
