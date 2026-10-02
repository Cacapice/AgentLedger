use std::collections::HashMap;

#[derive(Clone, Debug)]
pub struct RunState {
    pub run_id: String,
    pub status: String,
    pub step: Option<String>,
    pub lease_token: Option<String>,
    pub revision: u64,
}

pub struct RunStore {
    runs: HashMap<String, RunState>,
}

impl RunStore {
    pub fn new() -> Self {
        Self {
            runs: HashMap::new(),
        }
    }

    pub fn create(&mut self, id: &str) -> Result<RunState, String> {
        if self.runs.contains_key(id) {
            return Err("run exists".into());
        }
        let r = RunState {
            run_id: id.into(),
            status: "PENDING".into(),
            step: None,
            lease_token: None,
            revision: 0,
        };
        self.runs.insert(id.into(), r.clone());
        Ok(r)
    }

    pub fn acquire(&mut self, id: &str, token: &str) -> Result<RunState, String> {
        let r = self.runs.get_mut(id).ok_or("unknown run")?;
        r.status = "RUNNING".into();
        r.lease_token = Some(token.into());
        r.revision += 1;
        Ok(r.clone())
    }

    pub fn checkpoint(&mut self, id: &str, token: &str, step: &str) -> Result<RunState, String> {
        let r = self.runs.get_mut(id).ok_or("unknown run")?;
        if r.lease_token.as_deref() != Some(token) {
            return Err("stale fencing token".into());
        }
        r.step = Some(step.into());
        r.revision += 1;
        Ok(r.clone())
    }
}

impl Default for RunStore {
    fn default() -> Self {
        Self::new()
    }
}

pub fn valid_transition(a: &str, b: &str) -> bool {
    matches!(
        (a, b),
        ("PROPOSED", "AUTHORIZED")
            | ("PROPOSED", "CANCELLED")
            | ("AUTHORIZED", "ATTEMPTED")
            | ("AUTHORIZED", "CANCELLED")
            | ("ATTEMPTED", "COMMITTED")
            | ("ATTEMPTED", "FAILED")
            | ("ATTEMPTED", "UNKNOWN")
            | ("UNKNOWN", "COMMITTED")
            | ("UNKNOWN", "FAILED")
    )
}
