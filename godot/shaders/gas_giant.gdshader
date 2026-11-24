shader_type spatial;
#include "res://shaders/globe.gdshaderinc"
#include "res://shaders/impact_surface.gdshaderinc"
uniform vec4 tint : source_color = vec4(.96,.78,.56,1.);
uniform vec4 belt : source_color = vec4(.60,.36,.23,1.);
uniform sampler2D atlas : source_color, filter_linear_mipmap;
uniform bool storm=false;
uniform float u_time=0.;
varying vec3 p;
void vertex(){
	p=VERTEX;
	if(impact_age>=0.){
		float d=1.-dot(normalize(VERTEX),impact_dir);
		VERTEX*=1.-.26*exp(-11.*d)*impact_power;
	}
}
void fragment(){
	vec3 n=normalize(p); vec2 uv=globe_uv(n);
	float lat=n.y;
	float drift=u_time*.023*sin(lat*14.0);
	vec3 flow=vec3(n.x*3.1+drift,lat*10.,n.z*3.1);
	float eddy=terrain(flow);
	float v=.52+.23*sin(lat*40.0+eddy*3.1)+.16*sin(lat*71.0+eddy*6.5)+.08*sin(lat*139.0+eddy*8.0);
	if(quality_level>=1) v+=.11*sin(lat*204.+eddy*18.)+.07*noise3(flow*7.);
	if(quality_level>=2) v+=.095*sin(lat*408.+terrain(flow*1.9)*28.)-.10*terrain(flow*5.);
	if(impact_age>=0.){
		float dist=length(n-impact_dir);
		v+=.35*sin(lat*67.+impact_age*2.)*exp(-3.*dist);
		EMISSION=vec3(1.,.28,.04)*exp(-8.*dist)*impact_heat;
	}
	vec3 pigment=mix(belt.rgb,tint.rgb,v);
	if(storm) {
		vec2 delta=vec2(fract(uv.x-.69+.5)-.5,uv.y-.59);
		float r=length(delta*vec2(13.,29.))+.1*eddy;
		pigment=mix(pigment,vec3(.68,.23,.10)*(.8+.19*sin(r*20.)),1.-smoothstep(.48,.99,r));
	}
	vec2 advected=uv+vec2(.004*sin(lat*17.+u_time*.06),.0015*(eddy-.5));
	vec3 mapped=texture(atlas,advected).rgb;
	ALBEDO=mix(pigment,mapped*(.89+.18*v),storm ? .78 : .64); ROUGHNESS=.93;
}
