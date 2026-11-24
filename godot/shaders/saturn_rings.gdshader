shader_type spatial;
render_mode cull_disabled, depth_draw_never;
uniform vec4 tint : source_color = vec4(.92,.80,.66,1.);
void fragment(){
	float r=UV.x;
	float grain=.54+.19*sin(r*140.)+.12*sin(r*479.)+.07*sin(r*967.);
	float gap=smoothstep(.008,.022,abs(r-.61))*smoothstep(.003,.009,abs(r-.85));
	ALBEDO=tint.rgb*(.58+.40*grain);
	EMISSION=ALBEDO*.15;
	ALPHA=smoothstep(0.,.07,r)*(1.-smoothstep(.91,1.,r))*(.34+.65*grain)*gap;
}
