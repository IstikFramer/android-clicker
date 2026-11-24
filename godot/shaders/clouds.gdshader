shader_type spatial;
render_mode unshaded, depth_draw_never;
#include "res://shaders/globe.gdshaderinc"
uniform sampler2D cloud_map : filter_linear_mipmap;
uniform sampler2D damage_mask : hint_default_black;
uniform float damage_strength=0.0;
uniform vec4 tint : source_color = vec4(1);
uniform float density=0.70;
uniform float cover=0.0;
uniform float u_time=0.0;
uniform vec3 sun_dir_local=vec3(1,0,0);
varying vec3 p;
void vertex(){p=VERTEX;}
void fragment(){
	vec3 n=normalize(p); vec2 uv=globe_uv(n);
	float cloud=texture(cloud_map,uv+vec2(u_time*.0007,0)).a;
	float light=smoothstep(-.15,.95,dot(n,sun_dir_local));
	ALBEDO=tint.rgb*(.055+.95*light)*(.7+.3*cloud);
	ALPHA=(cover+(1.0-cover)*cloud)*density*(1.0-damage_strength*texture(damage_mask,uv).r);
}
