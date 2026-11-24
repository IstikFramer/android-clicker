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

    #[func]
    fn plan_impact(&self, fragments: Array<VarDictionary>, params: VarDictionary) -> VarDictionary {
        crate::convert::plan(&fragments, &params)
            .unwrap_or_else(|e| vdict! {"ok" => false,"error" => e.as_str()})
    }

    #[func]
    fn gravity_step(
        &self,
        positions: PackedVector3Array,
        masses: PackedFloat32Array,
        params: VarDictionary,
    ) -> PackedVector3Array {
        let values = (
            crate::convert::field(&params, "g_game"),
            crate::convert::field(&params, "epsilon"),
            crate::convert::field(&params, "max_acceleration"),
        );
        let (Ok(g), Ok(e), Ok(limit)) = values else {
            return PackedVector3Array::new();
        };
        if positions.len() > 96 {
            return PackedVector3Array::new();
        }
        let pos: Vec<_> = positions.as_slice().iter().copied().map(vector).collect();
        fracture_core::gravity::accelerations(&pos, masses.as_slice(), g, e, limit)
            .map(crate::convert::packed)
            .unwrap_or_default()
    }
}
