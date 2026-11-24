shader_type spatial;
#include "res://shaders/globe.gdshaderinc"
#include "res://shaders/impact_surface.gdshaderinc"
uniform vec4 tint : source_color = vec4(0.65,0.53,0.4,1);
uniform sampler2D day_map : source_color, hint_default_white, filter_linear_mipmap;
uniform sampler2D normal_map : hint_normal, filter_linear_mipmap;
uniform bool has_normal = false;
uniform float roughness = 0.89;
uniform int geology = 0;
varying vec3 p;
float crater_field(vec3 q){
	vec3 cell=floor(q);
	float d=2.;
	for(int i=-1;i<=1;i++){for(int j=-1;j<=1;j++){for(int k=-1;k<=1;k++){
		vec3 c=cell+vec3(float(i),float(j),float(k));
		vec3 center=c+.15+.7*vec3(h3(c),h3(c+12.),h3(c+35.));
		d=min(d,length(q-center));
	}}}
	return .22*exp(-80.*abs(d-.44))-.22*(1.-smoothstep(.18,.44,d));
}
void vertex() { p=fragment_coords ? NORMAL : VERTEX; }
void fragment() {
	vec3 n=normalize(p);
	float h=terrain(n*9.0);
	if(quality_level>=2) h+=.34*(terrain(n*61.)-.5);
	float value=0.48+0.66*h;
	if (geology==0) {
		value+=crater_field(n*11.);
		if(quality_level>=2){
			value+=.64*crater_field(n*29.+vec3(.7));
			value+=.19*(terrain(n*98.)-.5);
		}
	} else if (geology==2) {
		value-=0.31*exp(-13.0*abs(n.y+0.16+0.4*terrain(n*4.0)));
		if(quality_level>=2) value+=.19*sin(n.y*82.+terrain(n*13.)*9.)*(terrain(n*4.)-.12);
		value+=0.24*exp(-58.0*distance(n,normalize(vec3(-0.5,0.32,-0.81))));
	}
	vec2 uv=fragment_coords ? UV : globe_uv(n);
	ALBEDO=tint.rgb*texture(day_map,uv).rgb*value;
	if (geology!=0) ALBEDO=texture(day_map,uv).rgb*mix(.94,1.12,h)*(geology==2 ? vec3(1.24,1.,.97) : vec3(1.14,1.01,.90));
	if (geology==2) { ALBEDO=mix(ALBEDO,vec3(.83,.79,.72),smoothstep(.89,.975,abs(n.y)+0.045*h)); }
	if(impact_age>=0.) EMISSION=fissures(n);
	ROUGHNESS=roughness;
	if(has_normal){ NORMAL_MAP=texture(normal_map,uv).rgb; }
}
