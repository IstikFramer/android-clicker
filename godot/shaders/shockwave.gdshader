shader_type spatial;
render_mode unshaded,blend_add,cull_disabled,depth_draw_never;
uniform float strength=1.;
uniform bool shell=false;
void fragment(){
	float ring=shell ? pow(1.-abs(dot(normalize(NORMAL),normalize(VIEW))),3.) : exp(-42.*abs(length(UV*2.-1.)-.88));
	ALBEDO=mix(vec3(.32,.51,.83),vec3(1.,.71,.36),ring);
	ALPHA=ring*strength;
}
