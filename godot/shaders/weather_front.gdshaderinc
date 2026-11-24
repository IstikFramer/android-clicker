uniform float weather_age=-1.;
uniform float stripping=.45;
uniform float dispersal=0.;
uniform float weather_wave=1.;
uniform sampler2D old_cloud_scars : hint_default_black,filter_linear,repeat_enable;
float front_distance(vec3 n) {
	return acos(clamp(dot(n,impact_dir),-1.,1.));
}
float arrival(float angle) {
	return smoothstep(-.18,.34,weather_age-angle/(.82+stripping*1.8));
}
float wake_radius(float angle){
	return (1.-smoothstep(weather_wave*.67,weather_wave,angle));
}
vec3 weather_lift(vec3 n){
	if(weather_age<0.) return vec3(0);
	float a=front_distance(n);
	float f=arrival(a), wake=max(wake_radius(a),dispersal);
	vec3 along=n*dot(n,impact_dir)-impact_dir;
	float plume=.62+.38*sin(n.y*17.+n.z*12.+n.x*8.);
	return (n*(.035+.24*dispersal)*plume+along*.11)*wake*f*min(weather_age,2.4);
}
float weather_cover(vec3 n, float texture_density){
	float old=1.-texture(old_cloud_scars,globe_uv(n)).r;
	if(weather_age<0.) return old;
	float a=front_distance(n);
	float f=arrival(a);
	float erosion=f*max(wake_radius(a),dispersal*smoothstep(.0,2.8,weather_age));
	float tendril=.53+.47*sin(n.y*23.+n.x*9.+n.z*17.+texture_density*5.);
	float wisps=smoothstep(.06,.86,texture_density*.64+tendril*.36-erosion*.78);
	float remain=mix(1.,wisps*(1.-erosion),erosion);
	return old*remain*(1.-dispersal*smoothstep(2.1,3.9,weather_age));
}
