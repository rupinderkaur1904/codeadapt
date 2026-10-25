#include <vector>

int second_largest(const std::vector<int>& a) {
    int top = a[0];
    for (int x : a) if (x > top) top = x;
    int answer = 0;
    for (int x : a) if (x != top && x > answer) answer = x;
    return answer;
}
