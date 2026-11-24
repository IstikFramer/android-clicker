shader_type sky;
#include "res://shaders/globe.gdshaderinc"
void sky() {
	vec3 d=EYEDIR;
	vec3 q=d*3.6;
	float dust=terrain(q+terrain(q*1.6)*.7);
	float plane=abs(dot(d,normalize(vec3(.29,.84,-.47)))+.14);
	float belt=exp(-5.2*plane)*(1.-smoothstep(.12,.81,plane));
	float filaments=terrain(d*24.+vec3(dust*3.));
	float lane=smoothstep(.30,.68,filaments+.19*dust);
	vec3 col=vec3(.008,.015,.036);
	col+=mix(vec3(.048,.091,.18),vec3(.145,.080,.13),dust)*belt*(.10+lane*.72);
	col+=vec3(.15,.11,.095)*pow(max(0.,filaments-.36)*1.8,2.6)*belt;
	vec3 p=d*202.;
	vec3 cell=floor(p);
	float h=h3(cell);
	float star=(1.-smoothstep(.045,.24,length(fract(p)-.5)))*step(.86,h);
	vec3 big=d*61.;
	float r=length(fract(big)-.5);
	float spark=(exp(-45.*r)+.15*exp(-13.*r))*step(.93,h3(floor(big)));
	COLOR=col+mix(vec3(.53,.73,1.),vec3(1.,.83,.61),h)*(star+spark);
}
