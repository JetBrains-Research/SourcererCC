#include <vector>
#include <iostream>

using namespace std;

vector<int> t;
vector<vector<int>> g;

void dfs(int v) {
    for (int to : g[v]) {
        t.push_back(to);
        dfs(to);
    }
}

int main() {
    int n;
    cin >> n;
    g = vector<vector<int>>(n);
    for (int i = 0; i < n; i++) {
        g[i].append(i);
    }
    return 0;
}
