# How glsl-cow-*.png were made

They are new renders, not screenshots of the Qt application. `index.html` is a small WebGL 2
page that loads the project's own shader files from https://github.com/jichumao/GLSL-Shaders
(`glsl/surface/*.glsl`, `glsl/post/*.glsl`) and runs them on `objs/cow.obj` from the same
repository: the surface shader draws into a texture, then a post-process shader draws that
texture to the screen, as the application does.

The shader files are used as they are, apart from the `#version` line, which WebGL requires
to be `#version 300 es` with a precision statement. Shaders that rely on desktop GLSL's implicit
int-to-float conversion (lambert, deform, worleywarp, myshader) do not compile under WebGL and are not used.
The cow's normals are averaged per vertex so that the surface shades smoothly.

To rebuild: copy `glsl/`, `objs/cow.obj` and `textures/matcaps/` (as `matcaps/`) next to
`index.html`, serve the folder with `python3 -m http.server 8770`, then
`python3 run.py looks-final.json <out dir>` (needs Playwright and Chrome).
