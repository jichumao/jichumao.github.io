// Stand-in for the plugin's matrix.h (an old template library that current GCC rejects).
// It reproduces only what LSystem.cpp uses: RotationMatrix, with the same entries,
// the matrix product and the point transform. LSystem.cpp itself is compiled unchanged.
#ifndef TREE_MATRIX_SHIM_H
#define TREE_MATRIX_SHIM_H
#include <cmath>
#include "vec.h"
namespace math {
template <class T> class RotationMatrix {
public:
    T m[3][3];
    RotationMatrix() { for (int i = 0; i < 3; i++) for (int j = 0; j < 3; j++) m[i][j] = T(i == j); }
    RotationMatrix(int axis, double a) {
        T c = T(cos(a)), s = T(sin(a));
        if (axis == 0)      { T v[3][3] = {{1, 0, 0}, {0, c, -s}, {0, s, c}};  set(v); }
        else if (axis == 1) { T v[3][3] = {{c, 0, s}, {0, 1, 0}, {-s, 0, c}};  set(v); }
        else                { T v[3][3] = {{c, -s, 0}, {s, c, 0}, {0, 0, 1}};  set(v); }
    }
    RotationMatrix(const vec3& c1, const vec3& c2, const vec3& c3) {
        for (int i = 0; i < 3; i++) { m[i][0] = T(c1[i]); m[i][1] = T(c2[i]); m[i][2] = T(c3[i]); }
    }
private:
    void set(T v[3][3]) { for (int i = 0; i < 3; i++) for (int j = 0; j < 3; j++) m[i][j] = v[i][j]; }
};
template <class T> RotationMatrix<T> operator*(const RotationMatrix<T>& a, const RotationMatrix<T>& b) {
    RotationMatrix<T> r;
    for (int i = 0; i < 3; i++) for (int j = 0; j < 3; j++) { r.m[i][j] = 0; for (int k = 0; k < 3; k++) r.m[i][j] += a.m[i][k] * b.m[k][j]; }
    return r;
}
template <class T> vec3 operator*(const RotationMatrix<T>& a, const vec3& v) {
    return vec3(a.m[0][0] * v[0] + a.m[0][1] * v[1] + a.m[0][2] * v[2],
                a.m[1][0] * v[0] + a.m[1][1] * v[1] + a.m[1][2] * v[2],
                a.m[2][0] * v[0] + a.m[2][1] * v[1] + a.m[2][2] * v[2]);
}
}
#endif
