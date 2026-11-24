shader_type spatial;
render_mode unshaded, blend_add, cull_front, depth_draw_never;
uniform vec4 tint : source_color = vec4(.22,.55,1.,1.);
uniform vec3 sun_dir_local=vec3(1,0,0);
varying vec3 p;
void vertex(){p=VERTEX;}
void fragment(){
	float edge=pow(max(0.0,1.0-abs(dot(normalize(NORMAL),normalize(VIEW)))),3.2);
	float day=smoothstep(-.22,.72,dot(normalize(p),sun_dir_local));
	ALBEDO=tint.rgb;
	ALPHA=edge*(.09+.83*day)*smoothstep(0.0,.16,abs(dot(normalize(NORMAL),normalize(VIEW))));
}
