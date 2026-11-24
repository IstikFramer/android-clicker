extends Control

func _draw() -> void:
	var tint:=Color(.63,.93,1.,.91)
	var c:=size*.5
	for i in 4:
		var a:=i*PI*.5
		draw_arc(c,16.,a+.14,a+.83,10,Color(.015,.036,.06,.82),4.,true)
		draw_arc(c,16.,a+.14,a+.83,10,tint,1.8,true)
		var d:=Vector2.from_angle(a)
		draw_line(c+d*18.,c+d*24.,tint,1.5,true)
	draw_circle(c,1.6,Color(1.,.84,.56))
