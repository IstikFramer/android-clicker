shader_type spatial;
render_mode unshaded, cull_disabled;
uniform float drive = 0.;
void fragment() {
	vec2 p = UV*2.-1.;
	float r = length(p);
	if(r>.99) discard;
	float a = atan(p.y,p.x);
	float blade = .5+.5*cos(14.*a+5.*r);
	float plates = smoothstep(.17,.83,blade);
	vec3 metal = mix(vec3(.028,.046,.066),vec3(.18,.26,.29),plates)*(.5+.5*r);
	float slit = exp(-80.*abs(r-.63))*(.3+.7*plates)+exp(-90.*abs(r-.92));
	float filament = (.5+.5*cos(8.*a-5.*r+drive*4.))*exp(-12.*r*r);
	float glow = (filament*.31+slit+.39*exp(-23.*r*r))*(.63+1.65*drive);
	ALBEDO = metal+glow*vec3(.065,.60,.91)+vec3(.80,.54,.30)*pow(max(0.,1.-r*5.),4.)*drive;
}
