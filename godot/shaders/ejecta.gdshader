shader_type spatial;
render_mode unshaded,blend_mix,cull_disabled,depth_draw_never;
void vertex(){
	MODELVIEW_MATRIX=VIEW_MATRIX*mat4(INV_VIEW_MATRIX[0],INV_VIEW_MATRIX[1],INV_VIEW_MATRIX[2],MODEL_MATRIX[3]);
	MODELVIEW_MATRIX[0].xyz*=length(MODEL_MATRIX[0].xyz);
	MODELVIEW_MATRIX[1].xyz*=length(MODEL_MATRIX[1].xyz);
}
void fragment(){
	float r=length(UV*2.-1.);
	ALBEDO=COLOR.rgb;
	ALPHA=COLOR.a*(1.-smoothstep(.10,1.,r));
}
