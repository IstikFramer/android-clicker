shader_type spatial;
render_mode unshaded,blend_add,cull_disabled,depth_draw_never;
uniform float heat=1.;
void fragment(){
	vec2 p=UV*2.-1.;
	float r=length(p);
	float rim=exp(-24.*abs(r-.76))*(.68+.32*sin(atan(p.y,p.x)*19.));
	ALBEDO=mix(vec3(.42,.035,.012),vec3(1.,.52,.08),rim);
	ALPHA=clamp(rim+.06*(1.-smoothstep(.1,.72,r)),0.,1.)*heat;
}
