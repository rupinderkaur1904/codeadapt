#include <cstddef>
#include <vector>

// Advances past zeros in decreasing power-of-two steps, then returns the next index.
int first_true(const std::vector<int>& flags) {
    const std::size_t n = flags.size();
    std::size_t step = 1;
    while (step * 2 <= n) step *= 2;
    std::size_t zeros = 0;  // flags[0 .. zeros) are known to be 0
    for (; step > 0; step /= 2) {
        if (zeros + step <= n && flags[zeros + step - 1] == 0) zeros += step;
    }
    return static_cast<int>(zeros);
}
