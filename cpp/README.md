# C++ Backend (Future)

This directory will contain the C++ implementation of performance-critical kernels.

## Plan

1. Identify hot paths via profiling (expected: Fengler spline QP solver, large-scale COS pricing).
2. Implement in C++17 using Eigen for linear algebra and CVXGEN/ECOS for QP.
3. Wrap with pybind11.
4. Migrate build backend from `hatchling` to `scikit-build-core`.
5. Add conditional compilation: if MSVC/gcc/clang + optional C++ extension found, build
   the extension; otherwise fall back to pure Python via the `backend` dispatch layer.

## Structure (to be added)

```
cpp/
├── CMakeLists.txt
├── src/
│   ├── fengler_qp/
│   ├── cos_pricing/
│   └── pybind11_bindings.cpp
└── tests/
```

## Not Yet Implemented

- Do not add code to this directory until performance profiling indicates necessity.
- All numerical algorithms have pure-Python reference implementations in `qmath/`.
