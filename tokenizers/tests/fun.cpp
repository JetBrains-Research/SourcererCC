#include <vector>

using namespace std;

vector<int> t;

void dfs(int v) {
    for (int to : g[v]) {
        t.push_back(to);
        dfs(to);
    }
}
