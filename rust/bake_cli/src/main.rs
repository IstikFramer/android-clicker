//! Validate local hit directions supplied as JSON, one per line.
use fracture_core::model::HitDirection;
use std::io::{self, BufRead};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    for line in io::stdin().lock().lines() {
        let direction: HitDirection = serde_json::from_str(&line?)?;
        println!("{}", serde_json::to_string(&direction)?);
    }
    Ok(())
}
