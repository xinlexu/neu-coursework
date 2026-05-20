# UI PREDICTION SYSTEM

**Author:** Xinle Xu
**Date:** November 20, 2025

## Setup

### Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

Python version: 3.8+

### Data

Place the provided data files in the `data/` directory:

- `data/train_logs.csv`
- `data/validation_public.csv`

This public copy includes small support/public files only. Large local logs, generated pickle files, trained models, and result images are intentionally omitted.

The scripts will generate additional intermediate and output files inside `data/`, `models/`, and `results/`.

## Running the Code

Execute the scripts in this order from the project root:

1. **Preprocessing**

```bash
python code/preprocess.py
```

Output:

- `data/cleaned_logs.csv`
- `results/preprocess_log.txt`

2. **Feature Engineering**

```bash
python code/feature_engineering.py
```

Outputs:

- `data/train.pkl`
- `data/val.pkl`
- `data/test.pkl`
- `results/feature_engineering_log.txt`

Note: I chose `N = 10` for the sequence length when building sequences.

3. **Baseline Model**

```bash
python code/baseline.py
```

Output:

- `results/baseline_results.txt`

4. **LSTM Training**

```bash
python code/train_lstm.py
```

Outputs:

- `models/model_lstm.pth`
- `models/screen_encoder.pkl`
- `models/event_encoder.pkl`
- `models/element_encoder.pkl`
- `results/training_curves.png`
- `results/hyperparameter_comparison.png`
- `results/lstm_results.txt`
- `results/hyperparameter_search.txt`
- `results/confusion_matrix.png`

5. **Persona Clustering**

```bash
python code/persona_features.py
python code/clustering.py
```

Outputs:

- `models/user_feature_scaler.pkl`
- `models/kmeans_model.pkl`
- `data/user_personas.csv`
- `results/cluster_visualization.png`
- `results/cluster_analysis.txt`

6. **Simulation and Validation**

```bash
python code/simulate.py
python code/validation.py
```

Outputs:

- `data/synthetic_logs.csv`
- `results/validation_report.txt`

## Results Summary

- LSTM Test Top-1 Accuracy: **6.61%**
- LSTM Test Top-3 Accuracy: **19.91%**
- Baseline Test Top-1 Accuracy: **6.58%**
- Baseline Test Top-3 Accuracy: **20.03%**
- Optimal K: **4** clusters
- Validation verdict (real vs synthetic sessions): **FAIL**
- Best Hyperparameters (LSTM):
  - `embedding_dim = 128`
  - `hidden_dim = 256`
  - `num_layers = 2`
  - `dropout = 0.3`
  - `learning_rate = 0.001`
  - `batch_size = 64`

## Assumptions

1. Sessions with more than 50 events are kept in the dataset and treated as valid but rare behavior; no additional filtering is applied beyond the provided preprocessing rules.
2. Missing or unknown categorical values (for example, `element_id`) are mapped to a dedicated "unknown" token before encoding.
3. For simulation, each persona uses the same global LSTM model; up to 100 users per persona are sampled when generating synthetic sessions.
4. Random seeds are fixed inside the scripts where relevant, but exact results may vary slightly across different hardware and library versions.

## Notes

- Some statistical tests in `validation.py` can produce runtime warnings (for example, divide-by-zero in the chi-square calculation) when certain screens appear only in synthetic or only in real data. These warnings do not prevent the script from finishing and reflect strong distribution mismatches between real and simulated sessions.
- The project was developed and tested on a Windows machine using a local virtual environment.
