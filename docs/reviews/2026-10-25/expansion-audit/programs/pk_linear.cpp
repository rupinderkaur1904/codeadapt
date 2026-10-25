#include <vector>
int peak_index(const std::vector<int>& a) { int i = 0; while (i + 1 < (int)a.size() && a[i + 1] > a[i]) ++i; return i; }
