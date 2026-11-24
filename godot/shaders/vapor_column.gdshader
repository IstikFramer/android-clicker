shader_type spatial;
render_mode unshaded, cull_back, depth_draw_never;
#include "res://shaders/globe.gdshaderinc"
uniform vec4 pigment : source_color;
uniform float age=0.;
uniform float density=.3;
uniform float curl=1.;
varying vec3 coord;
void vertex() {
	coord=VERTEX;
	float h=coord.y+.5;
	float turn=h*3.+age*.84;
	float ripple=.84+.22*sin(coord.y*11.+coord.z*6.-age*1.4);
	VERTEX.xz*=ripple;
	VERTEX.xz+=h*h*vec2(sin(turn),cos(turn))*.28*curl;
}
void fragment() {
	vec3 uvw=coord*vec3(8.,5.,8.)+vec3(age*.09,-age*.34,age*.11);
	float billow=terrain(uvw+vec3(terrain(uvw*1.7+age*.17)));
	float edge=abs(dot(normalize(NORMAL),normalize(VIEW)));
	float smoke=smoothstep(.27,.66,billow)*smoothstep(.0,.28,edge);
	ALBEDO=mix(pigment.rgb*.42,pigment.rgb*1.23,clamp(billow+edge*.23,0.,1.));
	ALPHA=density*smoke;
}
