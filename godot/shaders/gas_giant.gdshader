shader_type spatial;
#include "res://shaders/globe.gdshaderinc"
uniform vec4 tint : source_color = vec4(.96,.78,.56,1.);
uniform vec4 belt : source_color = vec4(.60,.36,.23,1.);
uniform bool storm=false;
uniform float u_time=0.;
varying vec3 p;
void vertex(){p=VERTEX;}
void fragment(){
	vec3 n=normalize(p); vec2 uv=globe_uv(n);
	float lat=n.y;
	float drift=u_time*.023*sin(lat*14.0);
	vec3 flow=vec3(n.x*3.1+drift,lat*10.,n.z*3.1);
	float eddy=terrain(flow);
	float v=.52+.23*sin(lat*40.0+eddy*3.1)+.16*sin(lat*71.0+eddy*6.5)+.08*sin(lat*139.0+eddy*8.0);
	vec3 pigment=mix(belt.rgb,tint.rgb,v);
	if(storm) {
		vec2 delta=vec2(fract(uv.x-.69+.5)-.5,uv.y-.59);
		float r=length(delta*vec2(13.,29.))+.1*eddy;
		pigment=mix(pigment,vec3(.68,.23,.10)*(.8+.19*sin(r*20.)),1.-smoothstep(.48,.99,r));
	}
	ALBEDO=pigment; ROUGHNESS=.93;
}
