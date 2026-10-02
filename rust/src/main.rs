use serde::Deserialize;
use std::{env, fs};

#[derive(Deserialize)]
struct Root {
    cases: Vec<Case>,
}

#[derive(Deserialize)]
struct Case {
    name: String,
    transitions: Vec<String>,
    valid: bool,
}

fn main() {
    let a: Vec<String> = env::args().collect();
    if a.len() < 3 || a[1] != "conformance" {
        println!("usage: agentledger-runtime conformance <fixture>");
        return;
    }
    let f: Root = serde_json::from_str(&fs::read_to_string(&a[2]).unwrap()).unwrap();
    for c in f.cases {
        let ok = c
            .transitions
            .windows(2)
            .all(|w| agentledger_runtime::valid_transition(&w[0], &w[1]));
        assert_eq!(ok, c.valid, "{}", c.name)
    }
    println!("Rust conformance: OK")
}
