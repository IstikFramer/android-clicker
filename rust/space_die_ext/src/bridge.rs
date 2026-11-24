use fracture_core::targeting;
use glam::{Vec2, Vec3};
use godot::prelude::*;

fn vector(v: Vector3) -> Vec3 {
    Vec3::new(v.x, v.y, v.z)
}

fn direction(v: Option<Vec3>) -> Vector3 {
    v.map(|p| Vector3::new(p.x, p.y, p.z))
        .unwrap_or(Vector3::ZERO)
}

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

    #[func]
    fn globe_uv(&self, local_direction: Vector3) -> Vector2 {
        targeting::globe_uv(vector(local_direction))
            .map(|uv| Vector2::new(uv.x, uv.y))
            .unwrap_or(Vector2::new(-1.0, -1.0))
    }

    #[func]
    fn globe_direction(&self, uv: Vector2) -> Vector3 {
        direction(targeting::globe_direction(Vec2::new(uv.x, uv.y)))
    }

    #[func]
    fn pick_globe(&self, origin: Vector3, ray: Vector3, radius: f32) -> Vector3 {
        direction(targeting::pick_direction(
            vector(origin),
            vector(ray),
            radius,
        ))
    }
}
