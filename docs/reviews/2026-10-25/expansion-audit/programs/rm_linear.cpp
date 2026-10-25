#include <vector>
int rotated_min_index(const std::vector<int>& a) { int b = 0; for (int i = 1; i < (int)a.size(); ++i) if (a[i] < a[b]) b = i; return b; }
