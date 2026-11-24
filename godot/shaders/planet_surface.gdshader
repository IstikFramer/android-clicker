shader_type spatial;

// Procedural basalt ridges in local coordinates, continuous across the UV seam.
varying vec3 local_pos;
float hash(vec3 p) { return fract(sin(dot(p,vec3(41.1,74.7,119.3)))*4375.13); }
float noise3(vec3 p) {
	vec3 i=floor(p), f=fract(p);
	f=f*f*(3.0-2.0*f);
	vec2 h=vec2(0,1);
	return mix(mix(mix(hash(i),hash(i+h.yxx),f.x),mix(hash(i+h.xyx),hash(i+h.yyx),f.x),f.y),
		mix(mix(hash(i+h.xxy),hash(i+h.yxy),f.x),mix(hash(i+h.xyy),hash(i+h.yyy),f.x),f.y),f.z);
}
void vertex() { local_pos=VERTEX; }
void fragment() {
	vec3 p = normalize(local_pos);
	float ridges = noise3(p*4.0) + 0.35*noise3(p*11.0) + 0.18*noise3(p*28.0);
	float strata = sin(ridges*23.0+p.y*7.0) * 0.08;
	ALBEDO = mix(vec3(0.13,0.07,0.065),vec3(0.82,0.50,0.28),smoothstep(0.28,1.15,ridges+strata));
	ROUGHNESS = 0.95;
}
