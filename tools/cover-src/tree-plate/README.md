# How tree-plate.png and tree-grow-*.png were made

They are not screenshots. They are the output of the Tree Creator plugin's own L-system
core, run outside Maya on the grammars that ship with the plugin, and drawn as SVG.

1. Clone https://github.com/jichumao/Tree-Creator and copy `MayaPlugin/src/LSystem.cpp`,
   `LSystem.h`, `vec.cpp` and `vec.h` into a folder `core/`. Those files are used unchanged
   apart from one line in `vec.h` (`#undef M_PI_2` before its own `M_PI_2`, which GCC needs).
2. Put `matrix-shim.h` there as `core/matrix.h`. The plugin's matrix library does not compile
   with current GCC; the shim reproduces the one class the turtle uses (`RotationMatrix`)
   with the same entries.
3. `g++ -std=c++14 -O2 -w -fpermissive -Icore driver.cpp core/LSystem.cpp core/vec.cpp -o driver`
4. `python3 plate.py <Tree-Creator>/MayaPlugin/plants <out dir>` writes the SVG pages
   (branch thickness comes from how many branches each segment carries), and `shot.py`
   renders them with headless Chrome at 2x.

Angles and iteration counts are the classic ones for these grammars and are printed under each plant.
