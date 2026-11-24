shader_type spatial;
render_mode unshaded;
#include "res://shaders/globe.gdshaderinc"
uniform int quality_level=1;
uniform float u_time=0.;
varying vec3 p;
void vertex(){p=VERTEX;}
void fragment(){
	vec3 n=normalize(p); vec3 cell=n*46.+u_time*.036;
	float f=abs(terrain(cell)-.48);
	if(quality_level>=2) f+=.2*abs(terrain(cell*4.1)-.48);
	float spots=smoothstep(.13,.39,terrain(n*8.+u_time*.009));
	float limb=smoothstep(0.,.8,abs(dot(NORMAL,VIEW)));
	ALBEDO=mix(vec3(1.,.23,.024),vec3(1.,.91,.50),clamp(f*3.0+limb*.47,0.,1.))*(.51+.49*spots);
}
