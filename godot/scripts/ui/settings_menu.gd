extends Control

var selectors: Dictionary[String, OptionButton] = {}

func _ready() -> void:
	for key: String in Settings.OPTIONS:
		var label := Label.new()
		label.text = key.to_upper()
		%Grid.add_child(label)
		var selector := OptionButton.new()
		selector.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		for item in Settings.OPTIONS[key]:
			selector.add_item(tr(item))
		%Grid.add_child(selector)
		selectors[key] = selector
	load_form(Settings.values)
	%Apply.pressed.connect(apply_form)
	%Back.pressed.connect(SceneRouter.show_menu)
	%Defaults.pressed.connect(load_form.bind(Settings.DEFAULTS))
	selectors["resolution"].grab_focus()

func load_form(values: Dictionary) -> void:
	for key in selectors:
		selectors[key].select(values[key])

func apply_form() -> void:
	var candidate := {}
	for key in selectors:
		candidate[key] = selectors[key].selected
	if Settings.save_settings(candidate) == OK:
		SceneRouter.show_menu()
	else:
		%Note.text = "SAVE_FAILED"
