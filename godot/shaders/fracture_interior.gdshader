shader_type spatial;
#include "res://shaders/globe.gdshaderinc"
uniform float heat=0.0;
varying vec3 rock;
void vertex(){rock=COLOR.rgb*2.0-1.0;}
void fragment(){
	float depth=1.0-length(rock);
	float large=terrain(rock*14.);
	float grains=terrain(rock*83.);
	float seam=1.-smoothstep(.015,.13,abs(large-.48));
	float vein=1.-smoothstep(.012,.045,abs(large-.48));
	float molten=clamp((pow(depth,1.6)*.97+vein*.54+grains*.06)*heat,0.,1.);
	vec3 basalt=mix(vec3(.049,.032,.028),vec3(.24,.122,.073),grains);
	ALBEDO=basalt*(.65+large*.7);
	vec3 lava=mix(vec3(.86,.072,.009),vec3(1.,.76,.25),smoothstep(.42,.85,depth+seam*.28));
	EMISSION=lava*molten*molten*1.65;
	ROUGHNESS=.91-.25*molten;
}
