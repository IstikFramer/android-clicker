shader_type spatial;
uniform vec4 paint : source_color;
uniform float finish = 0.0;
uniform float drive = 0.0;
varying vec3 local_pos;
varying vec3 local_normal;
void vertex() {
	local_pos = VERTEX;
	local_normal = NORMAL;
}
void fragment() {
	vec3 n = abs(normalize(local_normal));
	vec2 uv = n.y > max(n.x,n.z) ? local_pos.xz : (n.x > n.z ? local_pos.zy : local_pos.xy);
	vec2 grid = uv * vec2(1.7,2.3);
	grid.x += .32*mod(floor(grid.y),2.);
	vec2 cell = fract(grid);
	vec2 bevel = min(cell,1.-cell);
	float edge = min(bevel.x,bevel.y);
	float panel = smoothstep(.008,.035,edge);
	vec2 rivet = min(abs(cell-.085),abs(cell-.915));
	float bolt = 1.-smoothstep(.014,.030,length(rivet));
	float grain = sin(uv.y*254.+3.*sin(uv.x*29.));
	float stripe = (1.-smoothstep(.010,.026,abs(abs(local_pos.x)-.46))) * step(.4,n.y);
	float stencil = step(.75,fract(local_pos.z*2.7))*step(.0,local_pos.z);
	vec3 pigment = paint.rgb*(.73+.25*panel+.02*grain);
	pigment = mix(pigment,vec3(.79,.32,.066),stripe*(.46+.54*stencil)*panel);
	pigment = mix(pigment,vec3(.43,.51,.54),bolt*.61);
	ALBEDO = pigment;
	METALLIC = .39+.26*finish;
	ROUGHNESS = clamp(.55-.17*finish+.18*(1.-panel)+.018*grain,.23,.86);
	if(finish > 1.5) {
		float pulse = .5+.5*sin(local_pos.z*4.-drive*15.);
		ALBEDO = vec3(.016,.22,.28);
		EMISSION = vec3(.035,.55,.82)*(.55+.82*drive*pulse);
	}
}
