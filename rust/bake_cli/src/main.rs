use fracture_core::{model::HitDirection, voronoi};
use std::{
    env, fs,
    io::{self, BufRead},
    path::PathBuf,
};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = env::args().skip(1).collect();
    if args.is_empty() {
        for line in io::stdin().lock().lines() {
            let direction: HitDirection = serde_json::from_str(&line?)?;
            println!("{}", serde_json::to_string(&direction)?);
        }
        return Ok(());
    }
    let arg = |name: &str| {
        args.windows(2)
            .find(|p| p[0] == name)
            .map(|p| p[1].as_str())
            .ok_or_else(|| format!("Missing {name}"))
    };
    let output = PathBuf::from(arg("--output")?);
    if args.iter().any(|s| s == "--validate") {
        let data: voronoi::Bake = serde_json::from_slice(&fs::read(output)?)?;
        voronoi::validate(&data)?;
        println!(
            "{}: {} closed cells, volume {:.7}",
            data.planet_id,
            data.cells.len(),
            data.source_volume
        );
    } else {
        let data = voronoi::bake(
            arg("--planet")?,
            arg("--count")?.parse()?,
            arg("--seed")?.parse()?,
        )?;
        if let Some(dir) = output.parent() {
            fs::create_dir_all(dir)?;
        }
        fs::write(output, serde_json::to_vec(&data)?)?;
    }
    Ok(())
}
