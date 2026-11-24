extends PopupPanel

signal region_picked(row: Dictionary)
var ordered: Array = []

func _ready() -> void:
	CountryLookup.initialize()
	$Body/Search.text_changed.connect(filter_rows)
	$Body/List.item_selected.connect(select_row)
	$Body/Back.pressed.connect(hide)

func open() -> void:
	ordered = CountryLookup.rows.duplicate()
	ordered.sort_custom(func(a: Dictionary,b: Dictionary): return CountryLookup.localized(a).naturalnocasecmp_to(CountryLookup.localized(b)) < 0)
	ordered.push_front(CountryLookup.by_id[0])
	$Body/Search.clear()
	filter_rows("")
	popup_centered()
	$Body/Search.grab_focus()

func filter_rows(query: String) -> void:
	$Body/List.clear()
	for row: Dictionary in ordered:
		var title := CountryLookup.localized(row)
		if not query.is_empty() and not (title+" "+row.en+" "+row.code).to_lower().contains(query.to_lower()):
			continue
		var idx: int = $Body/List.add_item(title)
		$Body/List.set_item_metadata(idx,row)

func select_row(i: int) -> void:
	var row: Dictionary = $Body/List.get_item_metadata(i)
	hide()
	region_picked.emit(row)
