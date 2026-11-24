shader_type spatial;
render_mode unshaded, depth_draw_never;
#include "res://shaders/globe.gdshaderinc"
#include "res://shaders/impact_surface.gdshaderinc"
uniform sampler2D cloud_map : filter_linear_mipmap;
uniform sampler2D damage_mask : hint_default_black;
uniform float damage_strength=0.0;
uniform vec4 tint : source_color=vec4(1);
uniform float density=.7;
uniform float cover=0.;
uniform float u_time=0.;
uniform vec3 sun_dir_local=vec3(1,0,0);
varying vec3 p;
void vertex(){p=VERTEX;}
void fragment(){
	vec3 n=normalize(p);
	vec2 uv=globe_uv(n)+vec2(u_time*.0007,0);
	float cloud=texture(cloud_map,uv,quality_level==0 ? 2.2 : 0.).a;
	if(cover>.6 && quality_level>=1){
		float wind=terrain(vec3(n.x*5.,n.y*13.+u_time*.005,n.z*5.));
		cloud=clamp(.44+.26*sin(n.y*31.+wind*7.)+.30*cloud,0.,1.);
	}
	float mu=dot(n,sun_dir_local);
	float day=smoothstep(-.16,.86,mu);
	vec3 pigment=tint.rgb*(.035+day*.91);
	float alpha=cloud*.49;
	if(quality_level>0){
		float bank=texture(cloud_map,uv+vec2(-.003,.0015)).a;
		alpha=smoothstep(.025,.94,cloud)*(.76+.24*cloud);
		pigment=mix(vec3(.10,.16,.25),tint.rgb,day)*(.57+.50*cloud);
		if(quality_level>=2){
			alpha=clamp(alpha*1.12+.19*abs(bank-cloud),0.,1.);
			pigment+=max(0.,cloud-bank)*vec3(.54,.51,.45)*(.23+day);
			pigment+=vec3(.36,.112,.031)*exp(-9.*abs(mu-.06));
		}
	}
	float scar=1.;
	if(impact_age>=0.) {
		float angle=acos(clamp(dot(n,impact_dir),-1.,1.));
		scar=smoothstep(.08+impact_power*.96,.24+impact_power*1.24,angle);
		pigment+=vec3(.9,.51,.25)*surface_wave(n);
	}
	if(cover>.6 && quality_level>=2) pigment*=mix(vec3(.66,.42,.26),vec3(1.19,1.06,.86),cloud);
	ALBEDO=pigment;
	ALPHA=mix(alpha,1.,cover)*scar*density*(1.-damage_strength*texture(damage_mask,uv).r);
}
