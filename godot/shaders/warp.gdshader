shader_type spatial;
render_mode unshaded,blend_add,cull_disabled,depth_draw_never;
uniform float progress=0.;
uniform float intensity=0.;
uniform float compress=0.;
uniform float direction=1.;
float hash(float x){return fract(sin(x*73.37)*4197.2);}
void fragment(){
	float lane=floor(UV.x*147.);
	float r=hash(lane);
	float sliver=exp(-abs(fract(UV.x*147.)-.5)*mix(11.,32.,r));
	float phase=fract(UV.y*(2.3+r*3.)-direction*progress*(4.+r*6.)+r);
	float streak=sliver*smoothstep(.30,.79,phase)*(1.-smoothstep(.88,1.,phase));
	float ripple=exp(-55.*abs(UV.y-fract(progress*2.1)))*.17*compress;
	ALBEDO=mix(vec3(.12,.45,1.),vec3(.94,.72,.38),r*r);
	ALPHA=(1.35*streak+ripple)*intensity*smoothstep(.0,.07,UV.y);
}
