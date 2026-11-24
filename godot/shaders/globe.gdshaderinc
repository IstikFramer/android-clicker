// Planet-local direction. Godot's stock sphere UV seam is deliberately ignored.
vec2 globe_uv(vec3 p) {
	vec3 n = normalize(p);
	float lon = length(n.xz) < 0.000001 ? 0.0 : atan(n.z,n.x);
	return vec2(fract(lon/TAU+0.5), 0.5-asin(clamp(n.y,-1.0,1.0))/PI);
}
float h3(vec3 p) {
	p = fract(p*0.1031); p += dot(p,p.yzx+33.33);
	return fract((p.x+p.y)*p.z);
}
float noise3(vec3 p) {
	vec3 i=floor(p), f=fract(p);
	f=f*f*(3.0-2.0*f);
	return mix(mix(mix(h3(i),h3(i+vec3(1,0,0)),f.x),mix(h3(i+vec3(0,1,0)),h3(i+vec3(1,1,0)),f.x),f.y),
		mix(mix(h3(i+vec3(0,0,1)),h3(i+vec3(1,0,1)),f.x),mix(h3(i+vec3(0,1,1)),h3(i+1.0),f.x),f.y),f.z);
}
float terrain(vec3 p) { return noise3(p)*0.57 + noise3(p*2.13)*0.29 + noise3(p*4.38)*0.14; }
