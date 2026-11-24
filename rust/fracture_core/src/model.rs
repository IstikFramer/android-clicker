use glam::Vec3;
use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum DirectionError {
    #[error("expected a finite unit vector")]
    Invalid,
}

/// A local-space direction, without distance or scene scale.
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
#[serde(try_from = "Vec3", into = "Vec3")]
pub struct HitDirection(Vec3);

impl TryFrom<Vec3> for HitDirection {
    type Error = DirectionError;
    fn try_from(value: Vec3) -> Result<Self, Self::Error> {
        if value.is_finite() && value.is_normalized() {
            Ok(Self(value))
        } else {
            Err(DirectionError::Invalid)
        }
    }
}

impl From<HitDirection> for Vec3 {
    fn from(value: HitDirection) -> Self {
        value.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_invalid_directions_even_on_deserialization() {
        assert!(HitDirection::try_from(Vec3::NAN).is_err());
        assert!(serde_json::from_str::<HitDirection>("[0,0,0]").is_err());
        assert!(serde_json::from_str::<HitDirection>("[0,1,0]").is_ok());
    }
}
