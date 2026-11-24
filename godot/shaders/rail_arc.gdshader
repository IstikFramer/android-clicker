shader_type spatial;
render_mode unshaded,blend_add,cull_disabled,depth_draw_never;
uniform float charge=0.;
uniform float clock=0.;
void fragment(){
	float y=UV.y;
	float wave=sin(y*20.+floor(clock*18.)*2.3)*sin(y*3.1416)*.19+sin(y*66.+floor(clock*26.))*.07;
	float d=abs(UV.x-.5-wave);
	ALBEDO=mix(vec3(.19,.61,1.),vec3(.91,1.,1.),exp(-85.*d));
	ALPHA=(exp(-64.*d)+.23*exp(-14.*d))*charge;
}
