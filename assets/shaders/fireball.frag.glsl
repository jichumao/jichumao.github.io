#version 300 es

// This is a fragment shader. If you've opened this file first, please
// open and read lambert.vert.glsl before reading on.
// Unlike the vertex shader, the fragment shader actually does compute
// the shading of geometry. For every pixel in your program's output
// screen, the fragment shader is run for every bit of geometry that
// particular pixel overlaps. By implicitly interpolating the position
// data passed into the fragment shader by the vertex shader, the fragment shader
// can compute what color to apply to its pixel based on things like vertex
// position, light position, and vertex color.
precision highp float;

//uniform vec4 u_Color; // The color with which to render this instance of geometry.
uniform vec4 u_Color1;
uniform vec4 u_Color2;
uniform vec4 u_Color3;

uniform float u_Time;

// These are the interpolated values out of the rasterizer, so you can't know
// their specific values without knowing the vertices that contributed to them
in vec4 fs_Nor;
in vec4 fs_LightVec;
in vec4 fs_Col;
in vec3 fs_WorldPos;

out vec4 out_Col; // This is the final output color that you will see on your
                  // screen for the pixel that is currently being processed.


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

// Simple function to get a color based on a displacement value
vec3 getColor(float displacement) {
    // vec3 color1 = vec3(1.0, 0.5, 0.0); 
    // vec3 color2 = vec3(1.0, 1.0, 0.0); 
    // vec3 color3 = vec3(1.0, 0.0, 0.0); 
    vec3 color1 = u_Color1.xyz;
    vec3 color2 = u_Color2.xyz;
    vec3 color3 = u_Color3.xyz;
    if (displacement < 0.0) {
        return mix(color1, color2, displacement * -1.0);
    } else {
        return mix(color2, color3, displacement);
    }
}

// Bias function
float bias(float a, float b) {
    return pow(a, log(b) / log(0.5));
}

// Gain function
float gain(float a, float b) {
    return a < 0.5 ? bias(a * 2.0, b) / 2.0 : 1.0 - bias(1.0 - (a - 0.5) * 2.0, b) / 2.0;
}

void main()
{
        
        float distance = length(fs_WorldPos);
        float normalizedDistance = clamp((distance - 0.8) / 0.4, 0.0, 1.0); 

        normalizedDistance = smoothstep(0.0, 1.0, normalizedDistance);

        float biasGain = gain(normalizedDistance, 0.5);
        normalizedDistance = biasGain;
        vec3 color = getColor(normalizedDistance);

        // Compute final shaded color
        vec3 finalColor = color;
        out_Col = vec4(finalColor, u_Color1.a);
}
