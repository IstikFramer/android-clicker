shader_type spatial;
render_mode unshaded,blend_add,cull_disabled,depth_draw_never;
uniform float strength=1.;
uniform vec4 tint : source_color = vec4(1.,.71,.36,1.);
uniform bool shell=false;
void fragment(){
	float ring=shell ? pow(1.-abs(dot(normalize(NORMAL),normalize(VIEW))),3.) : exp(-42.*abs(length(UV*2.-1.)-.88));
	ALBEDO=mix(vec3(.32,.51,.83),tint.rgb,ring);
	ALPHA=ring*strength;
}
