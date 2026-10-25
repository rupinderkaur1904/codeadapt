// Batch driver for the L20 search (review evidence only). Reads one case per line in the
// harness's literal format and prints one result per line. Each call runs in a forked child
// with a 0.5 s timer, so a non-terminating program yields TLE and a crash yields RE.
#include <csignal>
#include <cstdio>
#include <iostream>
#include <sstream>
#include <string>
#include <sys/time.h>
#include <sys/wait.h>
#include <unistd.h>
#include <vector>

#if defined(KIND_VT)
int FN(const std::vector<int>& a, int target);
#elif defined(KIND_V)
int FN(const std::vector<int>& a);
#else
int FN(int x);
#endif

int main() {
    std::string line;
    while (std::getline(std::cin, line)) {
        std::istringstream in(line);
        std::vector<int> a;
        int target = 0, x = 0;
#if defined(KIND_VT) || defined(KIND_V)
        char mode; long long n; in >> mode >> n;
        for (long long i = 0; i < n; ++i) { int v; in >> v; a.push_back(v); }
#if defined(KIND_VT)
        in >> target;
#endif
#else
        in >> x;
#endif
        int fd[2];
        if (pipe(fd)) return 2;
        std::fflush(stdout);
        const pid_t pid = fork();
        if (pid == 0) {
            close(fd[0]);
            itimerval t{}; t.it_value.tv_usec = 500000;
            setitimer(ITIMER_REAL, &t, nullptr);
#if defined(KIND_VT)
            int r = FN(a, target);
#elif defined(KIND_V)
            int r = FN(a);
#else
            int r = FN(x);
#endif
            if (write(fd[1], &r, sizeof r) != sizeof r) _exit(3);
            _exit(0);
        }
        close(fd[1]);
        int status = 0, r = 0;
        const bool got = read(fd[0], &r, sizeof r) == sizeof r;
        close(fd[0]);
        waitpid(pid, &status, 0);
        if (WIFSIGNALED(status) && WTERMSIG(status) == SIGALRM) std::printf("TLE\n");
        else if (!got || !WIFEXITED(status) || WEXITSTATUS(status) != 0) std::printf("RE\n");
        else std::printf("%d\n", r);
    }
    return 0;
}
