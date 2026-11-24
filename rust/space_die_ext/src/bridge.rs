use godot::prelude::*;

#[derive(GodotClass)]
#[class(base=RefCounted, init)]
struct FractureBridge {
    base: Base<RefCounted>,
}

#[godot_api]
impl FractureBridge {
    #[func]
    fn get_api_version(&self) -> i64 {
        1
    }
}
