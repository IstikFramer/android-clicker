shader_type canvas_item;
render_mode unshaded;
uniform sampler2D scene_color : hint_screen_texture,repeat_disable,filter_linear;
uniform float sharpness=.25;
uniform float texel_scale=1.;
uniform float saturation=1.12;
void fragment(){
	vec2 uv=SCREEN_UV, d=SCREEN_PIXEL_SIZE*texel_scale;
	vec3 c=texture(scene_color,uv).rgb;
	// Estimate the best local diagonal at transitions in a sub-native 3D frame.
	if(texel_scale>1.01){
		vec2 grid=uv/d-0.5;
		vec2 origin=(floor(grid)+0.5)*d;
		vec2 f=fract(grid);
		vec3 nw=texture(scene_color,origin).rgb, ne=texture(scene_color,origin+vec2(d.x,0)).rgb;
		vec3 sw=texture(scene_color,origin+vec2(0,d.y)).rgb, se=texture(scene_color,origin+d).rgb;
		vec3 lum=vec3(.2126,.7152,.0722);
		float a=abs(dot(nw-se,lum)), b=abs(dot(ne-sw,lum));
		vec3 linear=mix(mix(nw,ne,f.x),mix(sw,se,f.x),f.y);
		// Piecewise linear triangles preserve the chosen diagonal through the pixel.
		vec3 delta=nw+se-ne-sw;
		float correction=(a<b ? min(f.x,f.y) : max(0.,f.x+f.y-1.))-f.x*f.y;
		float weight=smoothstep(.025,.18,abs(a-b));
		c=mix(c,linear+delta*correction,weight*.87);
	}
	if(sharpness>.001){
		vec3 l=texture(scene_color,uv-vec2(d.x,0)).rgb, r=texture(scene_color,uv+vec2(d.x,0)).rgb;
		vec3 u=texture(scene_color,uv-vec2(0,d.y)).rgb, b=texture(scene_color,uv+vec2(0,d.y)).rgb;
		vec3 lo=min(c,min(min(l,r),min(u,b))), hi=max(c,max(max(l,r),max(u,b)));
		float contrast=max(hi.r-lo.r,max(hi.g-lo.g,hi.b-lo.b));
		float gain=sharpness*smoothstep(.018,.13,contrast)*(1.-.6*smoothstep(.35,.85,contrast));
		c=clamp(c+(c-(l+r+u+b)*.25)*gain,lo,hi);
	}
	float lum=dot(c,vec3(.2126,.7152,.0722));
	vec3 graded=mix(vec3(lum),c,saturation);
	graded+=vec3(-.009,.001,.012)*(1.-smoothstep(.03,.32,lum))*smoothstep(.0,.035,lum);
	COLOR=vec4(clamp(graded,vec3(0),vec3(1)),1.);
}
