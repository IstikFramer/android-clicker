uniform int quality_level=1;
uniform bool fragment_coords=false;
uniform vec3 impact_dir=vec3(1,0,0);
uniform float impact_age=-1.;
uniform float impact_power=0.;
uniform float impact_heat=0.;
float surface_wave(vec3 n){
	float angle=acos(clamp(dot(n,impact_dir),-1.,1.));
	return exp(-34.*abs(angle-impact_age*1.12))*exp(-impact_age*.6);
}
vec3 fissures(vec3 n) {
	if(impact_age<0. || impact_heat<=0.) return vec3(0);
	float angle=acos(clamp(dot(n,impact_dir),-1.,1.));
	float spread=min(3.2,.25+impact_age*.98+impact_power*.65);
	float mask=(1.-smoothstep(spread*.65,spread,angle))*(1.-smoothstep(.1+2.7*impact_power,.6+2.8*impact_power,angle));
	float line=abs(terrain(n*8.5+vec3(.4,0.,.9))-.51);
	return vec3(1.,.25,.027)*(1.-smoothstep(.003,.026,line))*mask*impact_heat;
}
