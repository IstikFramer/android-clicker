shader_type sky;
#include "res://shaders/globe.gdshaderinc"
void sky() {
	vec3 d=EYEDIR;
	float band=exp(-7.0*abs(dot(d,normalize(vec3(.33,.85,-.4)))+.13));
	float haze=band*terrain(d*9.)*.45;
	vec3 col=mix(vec3(.008,.014,.025),vec3(.13,.18,.25),haze);
	vec3 p=d*210.;
	vec3 cell=floor(p);
	float h=h3(cell);
	vec3 offset=fract(p)-.5;
	float star=(1.-smoothstep(.065,.25,length(offset)))*step(.83,h);
	COLOR=col+mix(vec3(.62,.79,1),vec3(1,.86,.67),h)*star;
}
