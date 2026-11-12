#version 300 es

//This is a vertex shader. While it is called a "shader" due to outdated conventions, this file
//is used to apply matrix transformations to the arrays of vertex data passed to it.
//Since this code is run on your GPU, each vertex is transformed simultaneously.
//If it were run on your CPU, each vertex would have to be processed in a FOR loop, one at a time.
//This simultaneous transformation allows your program to run much faster, especially when rendering
//geometry with millions of vertices.

uniform mat4 u_Model;       // The matrix that defines the transformation of the
                            // object we're rendering. In this assignment,
                            // this will be the result of traversing your scene graph.

uniform mat4 u_ModelInvTr;  // The inverse transpose of the model matrix.
                            // This allows us to transform the object's normals properly
                            // if the object has been non-uniformly scaled.

uniform mat4 u_ViewProj;    // The matrix that defines the camera's transformation.
                            // We've written a static matrix for you to use for HW2,
                            // but in HW3 you'll have to generate one yourself

uniform float u_Time;

uniform vec4 u_Color1;
uniform vec4 u_Color2;
uniform vec4 u_Color3;

uniform float u_Amplitude;
uniform float u_Frequency;

in vec4 vs_Pos;             // The array of vertex positions passed to the shader

in vec4 vs_Nor;             // The array of vertex normals passed to the shader

in vec4 vs_Col;             // The array of vertex colors passed to the shader.

out vec4 fs_Nor;            // The array of normals that has been transformed by u_ModelInvTr. This is implicitly passed to the fragment shader.
out vec4 fs_LightVec;       // The direction in which our virtual light lies, relative to each vertex. This is implicitly passed to the fragment shader.
out vec4 fs_Col;            // The color of each vertex. This is implicitly passed to the fragment shader.

out vec3 fs_WorldPos;

//const vec4 lightPos = vec4(0, 10, 0, 1); //The position of our virtual light, which is used to compute the shading of
                                        //the geometry in the fragment shader.

vec3 random3(vec3 gridPoint) {
    float sinX = sin(gridPoint.x * 12.9898 + gridPoint.y * 78.233 + gridPoint.z * 54.578) * 43758.5453;
    float sinY = sin(gridPoint.y * 12.9898 + gridPoint.x * 78.233 + gridPoint.z * 54.578) * 43758.5453;
    float sinZ = sin(gridPoint.z * 12.9898 + gridPoint.y * 78.233 + gridPoint.x * 54.578) * 43758.5453;
    return fract(vec3(sinX, sinY, sinZ));
}

vec3 custom_pow(vec3 v, float exponent) {
    return vec3(pow(v.x, exponent), pow(v.y, exponent), pow(v.z, exponent));
}

float surflet3D(vec3 p, vec3 gridPoint) {
    vec3 t2 = abs(p - gridPoint);
    vec3 t = vec3(1.0) - 6.0 * custom_pow(t2, 5.0) + 15.0 * custom_pow(t2, 4.0) - 10.0 * custom_pow(t2, 3.0);
    vec3 gradient = normalize(random3(gridPoint) * 2.0 - vec3(1.0));
    vec3 diff = p - gridPoint;
    float height = dot(diff, gradient);
    return height * t.x * t.y * t.z;
}

float perlinNoise3D(vec3 p) {
    float surfletSum = 0.0;
    for (int dx = 0; dx <= 1; ++dx) {
        for (int dy = 0; dy <= 1; ++dy) {
            for (int dz = 0; dz <= 1; ++dz) {
                vec3 gridPoint = floor(p) + vec3(float(dx), float(dy), float(dz));
                surfletSum += surflet3D(p, gridPoint);
            }
        }
    }
    return surfletSum;
}

// low frequency and amplitude 
float lowFreqDisplacement(vec3 pos, float time) {
    float displacement = sin(pos.x * 1.0 + time * 0.01) * 0.3 +
                         sin(pos.y * 0.5 + time * 0.01) * 0.3 +
                         sin(pos.z * 0.3 + time * 0.01) * 0.3;
    return 0.1 * displacement;
}

// high frequency and amplitude
float fbm(vec3 pos, float time) {
    float amplitude = u_Amplitude;
    float frequency = u_Frequency;
    float noise = 0.0;
    for(int i = 0; i < 4; i++) { // 4 layers of noise
        noise += amplitude * perlinNoise3D(pos * frequency + vec3(time * 0.1));
        amplitude *= 0.5;
        frequency *= 2.0;
    }
    return noise;
}

// Easing function: easeInOut
float easeOut(float t) {
    return t < 0.1 ? t : -1.0 + (4.0 - 2.0 * t) * t;
}

// Waves function using sine
float waves(float time, float frequency, float phase) {
    return sin(time * frequency + phase);
}

void main()
{
    fs_Col = vs_Col;                         
        
    mat3 invTranspose = mat3(u_ModelInvTr);
    fs_Nor = vec4(invTranspose * vec3(vs_Nor), 0);          // Pass the vertex normals to the fragment shader for interpolation.
                                                            // Transform the geometry's normals by the inverse transpose of the
                                                            // model matrix. This is necessary to ensure the normals remain
                                                            // perpendicular to the surface after the surface is transformed by
                                                            // the model matrix.

    float lowDisplacement = lowFreqDisplacement(vec3(vs_Pos), u_Time);

    //float highDisplacement = fbm(vec3(vs_Pos), u_Time);
    
    float easedTime = easeOut(mod(u_Time * 0.01, 3.0));

    float highDisplacement = fbm(vec3(vs_Pos) * easedTime, u_Time) + waves(0.0001 * u_Time, 5.0, 0.0) * 0.001;
    float totalDisplacement = lowDisplacement + highDisplacement;

    vec3 displacedPos = vec3(vs_Pos) + vec3(vs_Nor) * totalDisplacement;

    vec4 modelposition = u_Model * vec4(displacedPos, 1.0);

    //fs_LightVec = lightPos - modelposition;  // Compute the direction in which the light source lies
    fs_WorldPos = vec3(modelposition);
    gl_Position = u_ViewProj * modelposition;// gl_Position is a built-in variable of OpenGL which is
                                             // used to render the final positions of the geometry's vertices
}
