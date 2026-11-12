// Runs the Tree Creator plugin's own L-system core (LSystem.cpp, unchanged) outside Maya
// and prints the branch segments and flower positions it produces, as JSON.
#include "LSystem.h"
#include <cstdio>
#include <cstdlib>
int main(int argc, char** argv) {
    if (argc < 5) { fprintf(stderr, "usage: driver grammar.txt angle step iterations\n"); return 1; }
    LSystem l;
    l.loadProgram(argv[1]);
    l.setDefaultAngle((float)atof(argv[2]));
    l.setDefaultStep((float)atof(argv[3]));
    std::vector<LSystem::Branch> b; std::vector<LSystem::Geometry> g;
    l.process((unsigned)atoi(argv[4]), b, g);
    printf("{\"branches\":[");
    for (size_t i = 0; i < b.size(); i++)
        printf("%s[%.5g,%.5g,%.5g,%.5g,%.5g,%.5g]", i ? "," : "", b[i].first[0], b[i].first[1], b[i].first[2], b[i].second[0], b[i].second[1], b[i].second[2]);
    printf("],\"flowers\":[");
    for (size_t i = 0; i < g.size(); i++)
        printf("%s[%.5g,%.5g,%.5g,\"%s\"]", i ? "," : "", g[i].first[0], g[i].first[1], g[i].first[2], g[i].second.c_str());
    printf("]}\n");
    return 0;
}
