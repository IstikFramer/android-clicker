use godot::prelude::*;
mod bridge;

struct SpaceDieExtension;

// SAFETY: All exposed classes use the standard main-thread gdext lifecycle.
#[gdextension]
unsafe impl ExtensionLibrary for SpaceDieExtension {}
mod convert;
