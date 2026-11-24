extends ColorRect

signal region_picked(row: Dictionary)
var ordered: Array = []
var opener: Control

func _ready() -> void:
	CountryLookup.initialize()
	%Search.text_changed.connect(filter_rows)
	%List.item_selected.connect(select_row)
	%Close.pressed.connect(close)
	%Search.focus_previous = %Search.get_path_to(%Close)
	%Close.focus_next = %Close.get_path_to(%Search)

func open() -> void:
	ordered = CountryLookup.rows.duplicate()
	ordered.sort_custom(func(a: Dictionary,b: Dictionary): return CountryLookup.localized(a).naturalnocasecmp_to(CountryLookup.localized(b)) < 0)
	ordered.push_front(CountryLookup.by_id[0])
	%Search.clear()
	filter_rows("")
	opener = get_viewport().gui_get_focus_owner()
	show()
	%Search.grab_focus()

func filter_rows(query: String) -> void:
	%List.clear()
	for row: Dictionary in ordered:
		var title := CountryLookup.localized(row)
		if not query.is_empty() and not (title+" "+row.en+" "+row.code).to_lower().contains(query.to_lower()):
			continue
		var idx: int = %List.add_item(title)
		%List.set_item_metadata(idx,row)

func select_row(i: int) -> void:
	var row: Dictionary = %List.get_item_metadata(i)
	close()
	region_picked.emit(row)

func close() -> void:
	hide()
	if is_instance_valid(opener) and opener.is_visible_in_tree():
		opener.grab_focus()

func _input(event: InputEvent) -> void:
	if visible and event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		close()

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and not $Panel.get_global_rect().has_point(event.global_position):
		accept_event()
		close()
