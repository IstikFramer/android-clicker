shader_type canvas_item;
render_mode unshaded;
uniform int quality_level=1;

// The backdrop uses viewport-height units so stars and the limb stay circular.
float hash(vec2 p) {
	return fract(sin(dot(p, vec2(41.3, 289.1))) * 4375.83);
}
float noise2(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i+vec2(1,0)), f.x),
		mix(hash(i+vec2(0,1)), hash(i+1.0), f.x), f.y);
}
float grain_field(vec2 p) {
	return 0.53 * noise2(p) + 0.27 * noise2(p*2.07) + 0.13 * noise2(p*4.17) + 0.07 * noise2(p*8.1);
}
float stars(vec2 p, float freq, float threshold) {
	vec2 cell = floor(p * freq);
	vec2 at = vec2(hash(cell + 3.0), hash(cell + 21.0));
	float d = length(fract(p * freq) - at);
	return step(threshold,hash(cell + 53.0)) * exp(-175.0 * d*d);
}
void fragment() {
	float aspect = SCREEN_PIXEL_SIZE.y / SCREEN_PIXEL_SIZE.x;
	vec2 p = (UV - vec2(0.795,0.47)) * vec2(aspect,1.0);
	float radius = 0.337;
	vec2 q = p / radius;
	float radial = length(q);
	vec3 col = mix(vec3(0.021,0.030,0.046), vec3(0.066,0.088,0.107), grain_field(p*4.2));
	col += vec3(0.9,0.93,1.0) * (stars(p,119.0,0.92)*0.65 + stars(p,52.0,0.91));
	col += vec3(0.70,0.35,0.15) * exp(-19.0*abs(radial-1.02)) * max(0.0, -q.x*0.65-q.y*0.45);
	if (radial < 1.0) {
		vec3 n = vec3(q, sqrt(max(0.0,1.0-dot(q,q))));
		float latitude = n.y*0.92 - n.x*0.34;
		vec2 surface = vec2(atan(n.x,n.z)*2.0+TIME*0.012, latitude*5.0);
		float eddy = grain_field(surface*vec2(2.4,2.1));
		float belt = grain_field(vec2(surface.x*0.8, latitude*37.0+eddy*6.5));
		if(quality_level>=2) belt+=.16*grain_field(vec2(surface.x*3.1,latitude*103.+eddy*17.))-.07;
		float filaments = sin(latitude*139.0 + eddy*31.0) * (quality_level>=2 ? .094 : .025);
		vec3 pigment = mix(vec3(0.38,0.15,0.09),vec3(1.0,0.83,0.62),smoothstep(0.12,0.9,belt+filaments));
		float light = max(dot(n,normalize(vec3(-0.85,-0.36,0.32))),0.0);
		col = pigment * (0.035 + pow(light,0.76)) + vec3(0.012,0.017,0.023);
		col += vec3(0.66,0.41,0.22)*pow(1.0-n.z,3.5)*light;
	}
	// Dust rings, tilted in screen space and occluded by the near hemisphere.
	vec2 ring = mat2(vec2(0.95,0.312),vec2(-0.312,0.95)) * q;
	float orbit = length(vec2(ring.x, ring.y/0.20));
	if (orbit > 1.26 && orbit < 2.15 && (radial > 1.0 || ring.y > 0.0)) {
		float lanes = noise2(vec2(orbit*91.0,0.4))*0.44 + 0.46;
		lanes *= 1.0 - 0.84*smoothstep(0.017,0.0+0.028,0.045-abs(orbit-1.84));
		float dust = smoothstep(1.26,1.42,orbit)*(1.0-smoothstep(1.98,2.15,orbit));
		col = mix(col, mix(vec3(0.28,0.18,0.13),vec3(0.85,0.68,0.50),lanes), dust*lanes*0.94);
	}
	COLOR = vec4(col,1.0);
}
