# Sparse CA3 attractor implementation

This package implements the frozen v1.0 sparse binary autoassociative network
used to study CA3 pattern completion and competition between two overlapping
engrams.

## Package contents

| File | Purpose |
|---|---|
| `config.py` | Validated model parameters and runtime profiles |
| `engrams.py` | A/B layout, overlap, tag-source, and accessibility sampling |
| `model.py` | Recurrent attractor dynamics, cues, manipulations, and readouts |
| `theory_mapping.py` | Cue-support and neural-to-behavioral measurement mappings |
| `run_validation.py` | Attractor qualification across thresholds and seeds |
| `run_theory_experiments.py` | Cue basin and H1–H3 response surfaces |
| `run_robustness.py` | Sparsity-by-overlap robustness grid |
| `run_hypothesis_phase_map.py` | Joint overlap/access/strength phase map |
| `run_mechanism_ablations.py` | Recurrence, inhibition, and overlap ablations |
| `run_recall_probe_protocol.py` | Experiment-matched paired recall–probe protocol |
| `parameter_audit.py` | Explicit classification of all model parameters |
| `tests/test_sparse_attractor.py` | Unit and protocol-level regression tests |

## Core dynamics

Two equal-size binary patterns are generated with a specified overlap. The
centered pattern matrix `X` defines the covariance-Hebbian recurrent field:

```text
m(x)   = X x / [N a (1-a)]
h_rec  = recurrent_gain × (m(x) X - diagonal_coupling × x)
```

The diagonal term removes autapses exactly. This factorized computation is
mathematically equivalent to applying the dense two-pattern covariance matrix
with `W_ii = 0`.

At each update:

1. recurrent, cue, and manipulation fields are summed;
2. cells below the activation threshold are removed;
3. if necessary, the strongest cells are retained up to the sparse activity
   cap;
4. deterministic infinitesimal tie-breaking resolves exactly equal fields.

The network is iterated until a fixed point, a previously seen state, or the
configured maximum number of steps is reached.

## Engram and intervention sets

The following cellular sets remain distinct:

- final test-time A and B engrams;
- A-only, B-only, shared, and outside cells;
- the representation active during RAM tagging;
- tagged cells sampled from that representation;
- light-accessible tagged cells;
- the intersection between accessible tagged cells and final memory A.

This separation prevents tagging efficiency, optical coverage, and
representation stability from being collapsed into a single parameter.

## Cue construction

Pure and mixed cues use a fixed target-slot budget. For mixed evidence,
`lambda_A = cue_A / (cue_A + cue_B)` determines how many slots are allocated to
A versus B. Shared and unique cells are interleaved so nested cue sizes retain
approximately balanced shared-cell content.

The external cue can be removed after one or more update steps to test
autonomous completion. Manipulation fields can begin before the cue and remain
active during convergence.

## State readouts

Each state summary contains:

- covariance overlap with A and B;
- A-only, B-only, shared, and outside activity;
- neural competition index;
- signed retrieval evidence `E = A_only - B_only`;
- active fraction and attractor class;
- tagged reactivation and structural chance reactivation.

Attractor classes (`A`, `B`, `mixed`, `silent`, `undecided`) are determined by
explicit activity and competition thresholds in `model.py`.

## Commands

All commands are run from the repository root.

### Unit tests

```powershell
& .\.venv\Scripts\python.exe -m unittest discover `
  -s models\ca3_sparse_attractor\tests -v
```

### Independent attractor validation

```powershell
& .\.venv\Scripts\python.exe `
  -m models.ca3_sparse_attractor.run_validation `
  --profile pilot `
  --output outputs\ca3_sparse_attractor\independent_validation_pilot_v1.json
```

### Cue basins and hypothesis surfaces

```powershell
& .\.venv\Scripts\python.exe `
  -m models.ca3_sparse_attractor.run_theory_experiments `
  --profile pilot `
  --output outputs\ca3_sparse_attractor\theory_experiments_pilot_v2.json
```

### Sparsity-by-overlap robustness

```powershell
& .\.venv\Scripts\python.exe `
  -m models.ca3_sparse_attractor.run_robustness `
  --output outputs\ca3_sparse_attractor\robustness_overlap_sparsity_v1.json

& .\.venv\Scripts\python.exe `
  analysis\plot_sparse_attractor_robustness.py `
  --input outputs\ca3_sparse_attractor\robustness_overlap_sparsity_v1.json `
  --output outputs\ca3_sparse_attractor\robustness_overlap_sparsity_v1.png
```

### Joint H1–H3 phase map

```powershell
& .\.venv\Scripts\python.exe `
  -m models.ca3_sparse_attractor.run_hypothesis_phase_map `
  --output outputs\ca3_sparse_attractor\hypothesis_phase_map_v1.json

& .\.venv\Scripts\python.exe `
  analysis\summarize_hypothesis_phase_map.py `
  --input outputs\ca3_sparse_attractor\hypothesis_phase_map_v1.json `
  --json-output outputs\ca3_sparse_attractor\hypothesis_decision_report_v1.json `
  --markdown-output notes\15_hypothesis_decision_report_v1.md

& .\.venv\Scripts\python.exe `
  analysis\plot_hypothesis_phase_map.py `
  --input outputs\ca3_sparse_attractor\hypothesis_phase_map_v1.json `
  --strength 1.0 `
  --output outputs\ca3_sparse_attractor\hypothesis_phase_map_strength1_v1.png
```

### Mechanism ablations and parameter audit

```powershell
& .\.venv\Scripts\python.exe `
  -m models.ca3_sparse_attractor.run_mechanism_ablations `
  --output outputs\ca3_sparse_attractor\mechanism_ablations_v1.json

& .\.venv\Scripts\python.exe `
  -m models.ca3_sparse_attractor.parameter_audit `
  --output outputs\ca3_sparse_attractor\parameter_audit_v1.json
```

### Recall–probe protocol

```powershell
& .\.venv\Scripts\python.exe `
  -m models.ca3_sparse_attractor.run_recall_probe_protocol `
  --json-output outputs\ca3_sparse_attractor\recall_probe_protocol_v1.json `
  --csv-output outputs\ca3_sparse_attractor\recall_probe_trials_v1.csv `
  --markdown-output notes\16_recall_probe_protocol_v1.md

& .\.venv\Scripts\python.exe `
  analysis\plot_recall_probe_protocol.py `
  --input outputs\ca3_sparse_attractor\recall_probe_protocol_v1.json `
  --output outputs\ca3_sparse_attractor\recall_probe_protocol_v1.png
```

### Interactive phase-map viewer

```powershell
& .\.venv\Scripts\python.exe `
  analysis\build_ca3_hypothesis_lab.py `
  --phase-map outputs\ca3_sparse_attractor\hypothesis_phase_map_v1.json `
  --ablations outputs\ca3_sparse_attractor\mechanism_ablations_v1.json `
  --template analysis\templates\ca3-hypothesis-lab.fragment.html `
  --output apps\ca3_hypothesis_lab.fragment.html `
  --standalone-output apps\ca3_hypothesis_lab.html
```

## Interpretation boundary

The implementation tests attractor-level mechanisms and conditional model
predictions. Structural seeds quantify sensitivity to cellular layout; they do
not represent animals. Signed intervention fields do not reproduce biological
light delivery or opsin dynamics. Behavioral statistics require calibration
with pilot neural and behavioral measurements.
