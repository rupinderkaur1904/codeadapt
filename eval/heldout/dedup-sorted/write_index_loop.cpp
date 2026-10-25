#include <vector>

int remove_duplicates(std::vector<int>& a) {
    std::size_t write = 0;
    for (std::size_t read = 0; read < a.size(); ++read) {
        if (write == 0 || a[read] != a[write - 1]) a[write++] = a[read];
    }
    return static_cast<int>(write);
}
