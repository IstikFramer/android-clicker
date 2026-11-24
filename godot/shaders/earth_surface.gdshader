shader_type spatial;
#include "res://shaders/globe.gdshaderinc"
#include "res://shaders/impact_surface.gdshaderinc"
uniform sampler2D day_map : source_color, filter_linear_mipmap;
uniform sampler2D night_map : source_color, filter_linear_mipmap;
uniform sampler2D ocean_mask : filter_linear_mipmap;
uniform sampler2D cloud_map : filter_linear_mipmap;
uniform sampler2D damage_mask : hint_default_black;
uniform float damage_strength=0.;
uniform vec3 sun_dir_local=vec3(1,0,0);
uniform float u_time=0.;
varying vec3 p;
void vertex(){p=fragment_coords ? NORMAL : VERTEX;}
void fragment(){
	vec3 n=normalize(p);
	vec2 uv=fragment_coords ? UV : globe_uv(n);
	float mu=dot(n,sun_dir_local);
	float water=texture(ocean_mask,uv).r;
	vec3 pigment=texture(day_map,uv,quality_level==0 ? 1.6 : 0.).rgb;
	float intact=1.-clamp(texture(damage_mask,uv).r*damage_strength,0.,1.);
	ALBEDO=pigment*mix(.17,1.,intact);
	ROUGHNESS=mix(.87,.48,water);
	SPECULAR=mix(.12,.44,water);
	EMISSION=texture(night_map,uv).rgb*(1.-smoothstep(-.18,.09,mu))*intact*(quality_level>0 ? 1.3 : .54);
	if(quality_level>0){
		vec2 offset=(globe_uv(normalize(n+.013*sun_dir_local))-globe_uv(n));
		float shade=texture(cloud_map,uv+vec2(u_time*.0007,0)+offset).a;
		ALBEDO*=1.-shade*(quality_level>1 ? .44 : .22)*smoothstep(-.1,.4,mu);
		ROUGHNESS=mix(.82,.24,water);
		float rim=pow(1.-clamp(dot(normalize(NORMAL),normalize(VIEW)),0.,1.),3.);
		EMISSION+=vec3(.033,.17,.39)*rim*smoothstep(-.28,.42,mu);
	}
	if(quality_level>=2){
		vec2 texel=1.0/vec2(textureSize(day_map,0));
		float ridge=dot(texture(day_map,uv+texel*vec2(2.,-2.)).rgb-texture(day_map,uv-texel*vec2(2.,-2.)).rgb,vec3(.3,.59,.11));
		ALBEDO*=1.+clamp(ridge*1.1,-.095,.095)*(1.-water);
		vec3 halfvec=normalize(VIEW+mat3(VIEW_MATRIX)*mat3(MODEL_MATRIX)*sun_dir_local);
		EMISSION+=vec3(.62,.69,.71)*pow(max(0.,dot(halfvec,NORMAL)),77.)*water*smoothstep(.0,.3,mu);
	}
	if(impact_age>=0.){
		EMISSION+=fissures(n);
		if(impact_power>=.2) EMISSION+=vec3(.07,.57,.79)*surface_wave(n)*water;
	}
}
