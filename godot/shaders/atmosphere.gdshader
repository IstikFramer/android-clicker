shader_type spatial;
render_mode unshaded, blend_add, cull_front, depth_draw_never;
uniform vec4 tint : source_color=vec4(.22,.55,1.,1.);
uniform vec3 sun_dir_local=vec3(1,0,0);
uniform int quality_level=1;
uniform float air_fraction=1.;
uniform float impact_age=-1.;
uniform float impact_power=0.;
uniform vec3 impact_dir=vec3(1,0,0);
varying vec3 p;
void vertex(){p=VERTEX;}
void fragment(){
	float view_angle=abs(dot(normalize(NORMAL),normalize(VIEW)));
	float mu=dot(normalize(p),sun_dir_local);
	float day=smoothstep(-.26,.64,mu);
	float edge=exp(-(quality_level>=2 ? 3.8 : 6.6)*view_angle)*smoothstep(.0,.12,view_angle);
	vec3 dusk=vec3(.92,.26,.067)*exp(-9.*abs(mu+.02));
	ALBEDO=tint.rgb+(quality_level>=2 ? dusk : vec3(0));
	float scar=impact_age<0. ? 1. : smoothstep(.06+impact_power*.96,.24+impact_power*1.24,acos(clamp(dot(normalize(p),impact_dir),-1.,1.)));
	ALPHA=scar*air_fraction*edge*(.07+day*.89)*(quality_level==0 ? .44 : 1.);
}
