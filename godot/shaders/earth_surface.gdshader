shader_type spatial;
#include "res://shaders/globe.gdshaderinc"
uniform sampler2D day_map : source_color, filter_linear_mipmap;
uniform sampler2D night_map : source_color, filter_linear_mipmap;
uniform sampler2D ocean_mask : filter_linear_mipmap;
uniform sampler2D damage_mask : hint_default_black;
uniform float damage_strength : hint_range(0,1) = 0.0;
uniform vec3 sun_dir_local = vec3(1,0,0);
varying vec3 p;
void vertex(){ p=VERTEX; }
void fragment(){
	vec3 n=normalize(p);
	vec2 uv=globe_uv(n);
	float day=smoothstep(-.10,.17,dot(n,sun_dir_local));
	float water=texture(ocean_mask,uv).r;
	float intact=1.0-clamp(texture(damage_mask,uv).r*damage_strength,0.0,1.0);
	vec3 pigment=texture(day_map,uv).rgb;
	ALBEDO=mix(pigment*.17,pigment,intact);
	ROUGHNESS=mix(.82,.21,water);
	SPECULAR=mix(.16,.66,water);
	EMISSION=texture(night_map,uv).rgb*(1.0-day)*intact*1.32;
}
