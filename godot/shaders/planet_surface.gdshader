shader_type spatial;
#include "res://shaders/globe.gdshaderinc"
uniform vec4 tint : source_color = vec4(0.65,0.53,0.4,1);
uniform sampler2D day_map : source_color, hint_default_white, filter_linear_mipmap;
uniform sampler2D normal_map : hint_normal, filter_linear_mipmap;
uniform bool has_normal = false;
uniform float roughness = 0.89;
uniform int geology = 0;
varying vec3 p;
void vertex() { p=VERTEX; }
void fragment() {
	vec3 n=normalize(p);
	float h=terrain(n*9.0);
	float value=0.48+0.66*h;
	if (geology==0) {
		vec3 cell=floor(n*11.0);
		float d=2.0;
		for(int i=-1;i<=1;i++) { for(int j=-1;j<=1;j++) { for(int k=-1;k<=1;k++) {
			vec3 c=cell+vec3(float(i),float(j),float(k));
			vec3 center=c+0.15+0.7*vec3(h3(c),h3(c+12.0),h3(c+35.0));
			d=min(d,length(n*11.0-center));
		}}}
		value += 0.22*exp(-80.0*abs(d-0.44))-0.22*(1.0-smoothstep(0.18,0.44,d));
	} else if (geology==2) {
		value-=0.31*exp(-13.0*abs(n.y+0.16+0.4*terrain(n*4.0)));
		value+=0.24*exp(-58.0*distance(n,normalize(vec3(-0.5,0.32,-0.81))));
	}
	vec2 uv=globe_uv(n);
	ALBEDO=tint.rgb*texture(day_map,uv).rgb*value;
	if (geology==2) { ALBEDO=mix(ALBEDO,vec3(.83,.79,.72),smoothstep(.89,.975,abs(n.y)+0.045*h)); }
	ROUGHNESS=roughness;
	if(has_normal){ NORMAL_MAP=texture(normal_map,uv).rgb; }
}
