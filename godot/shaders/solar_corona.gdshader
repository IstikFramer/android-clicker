shader_type spatial;
render_mode unshaded, blend_add, cull_front, depth_draw_never;
#include "res://shaders/globe.gdshaderinc"
uniform float u_time=0.;
varying vec3 p;
void vertex(){p=VERTEX;}
void fragment(){
	float rim=abs(dot(normalize(NORMAL),normalize(VIEW)));
	float rays=terrain(normalize(p)*22.+u_time*.02);
	ALBEDO=vec3(1.,.41,.056);
	ALPHA=smoothstep(.04,.64,rim)*(.28+.62*rays);
}
