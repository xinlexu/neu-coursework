import json
import math
import pickle
from pathlib import Path
from typing import Dict, Any, List

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
RESULTS_DIR = ROOT / "results"


class LSTMNextScreen(nn.Module):
    def __init__(
        self,
        num_screens: int,
        num_events: int,
        embedding_dim: int,
        hidden_dim: int,
        num_layers: int,
        dropout: float,
    ) -> None:
        super().__init__()
        self.screen_emb = nn.Embedding(num_screens, embedding_dim)
        self.event_emb = nn.Embedding(num_events, embedding_dim)
        input_dim = embedding_dim * 2
        lstm_dropout = dropout if num_layers > 1 else 0.0
        self.lstm = nn.LSTM(
            input_dim,
            hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=lstm_dropout,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, num_screens)

    def forward(self, screens: torch.Tensor, events: torch.Tensor) -> torch.Tensor:
        emb_s = self.screen_emb(screens)
        emb_e = self.event_emb(events)
        x = torch.cat([emb_s, emb_e], dim=-1)
        out, _ = self.lstm(x)
        last = out[:, -1, :]
        last = self.dropout(last)
        logits = self.fc(last)
        return logits


def load_split(name: str):
    with open(DATA_DIR / f"{name}.pkl", "rb") as f:
        data = pickle.load(f)
    X = data["X"]
    y = data["y"]
    return X, y


def load_encoder(path: Path) -> Dict[str, Any]:
    with open(path, "rb") as f:
        enc = pickle.load(f)
    return enc


def build_datasets():
    X_train, y_train = load_split("train")
    X_val, y_val = load_split("val")
    X_test, y_test = load_split("test")

    X_train_s = torch.from_numpy(X_train[:, :, 0]).long()
    X_train_e = torch.from_numpy(X_train[:, :, 1]).long()
    X_val_s = torch.from_numpy(X_val[:, :, 0]).long()
    X_val_e = torch.from_numpy(X_val[:, :, 1]).long()
    X_test_s = torch.from_numpy(X_test[:, :, 0]).long()
    X_test_e = torch.from_numpy(X_test[:, :, 1]).long()

    y_train_t = torch.from_numpy(y_train).long()
    y_val_t = torch.from_numpy(y_val).long()
    y_test_t = torch.from_numpy(y_test).long()

    train_ds = TensorDataset(X_train_s, X_train_e, y_train_t)
    val_ds = TensorDataset(X_val_s, X_val_e, y_val_t)
    test_ds = TensorDataset(X_test_s, X_test_e, y_test_t)
    return train_ds, val_ds, test_ds, y_test


def accuracy_topk(logits: torch.Tensor, targets: torch.Tensor, k: int = 1) -> float:
    with torch.no_grad():
        topk = logits.topk(k, dim=1).indices
        if k == 1:
            preds = topk.squeeze(1)
            correct = (preds == targets).float().mean().item()
            return float(correct)
        matches = (topk == targets.unsqueeze(1)).any(dim=1).float().mean().item()
        return float(matches)


def run_training() -> None:
    MODELS_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)

    train_ds, val_ds, test_ds, y_test = build_datasets()

    screen_enc = load_encoder(MODELS_DIR / "screen_encoder.pkl")
    event_enc = load_encoder(MODELS_DIR / "event_encoder.pkl")
    num_screens = screen_enc["unknown_index"] + 1
    num_events = event_enc["unknown_index"] + 1

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    search_space: List[Dict[str, Any]] = [
        {"embedding_dim": 32, "hidden_dim": 64, "num_layers": 1, "dropout": 0.2, "learning_rate": 0.001, "batch_size": 64},
        {"embedding_dim": 64, "hidden_dim": 128, "num_layers": 1, "dropout": 0.3, "learning_rate": 0.001, "batch_size": 64},
        {"embedding_dim": 64, "hidden_dim": 128, "num_layers": 2, "dropout": 0.3, "learning_rate": 0.001, "batch_size": 64},
        {"embedding_dim": 128, "hidden_dim": 256, "num_layers": 2, "dropout": 0.3, "learning_rate": 0.001, "batch_size": 64},
        {"embedding_dim": 64, "hidden_dim": 256, "num_layers": 2, "dropout": 0.5, "learning_rate": 0.0005, "batch_size": 64},
    ]

    max_epochs = 20
    patience = 3

    best_overall_acc = 0.0
    best_overall_state = None
    best_overall_config: Dict[str, Any] = {}
    best_history: Dict[str, List[float]] = {}

    search_records: List[Dict[str, Any]] = []

    for idx, cfg in enumerate(search_space):
        model = LSTMNextScreen(
            num_screens=num_screens,
            num_events=num_events,
            embedding_dim=cfg["embedding_dim"],
            hidden_dim=cfg["hidden_dim"],
            num_layers=cfg["num_layers"],
            dropout=cfg["dropout"],
        ).to(device)

        optimizer = torch.optim.Adam(model.parameters(), lr=cfg["learning_rate"])
        criterion = nn.CrossEntropyLoss()

        train_loader = DataLoader(train_ds, batch_size=cfg["batch_size"], shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=cfg["batch_size"], shuffle=False)

        history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}
        best_val_acc = 0.0
        best_state = None
        no_improve = 0

        for epoch in range(1, max_epochs + 1):
            model.train()
            running_loss = 0.0
            running_correct = 0.0
            running_total = 0

            for screens, events, targets in train_loader:
                screens = screens.to(device)
                events = events.to(device)
                targets = targets.to(device)

                optimizer.zero_grad()
                logits = model(screens, events)
                loss = criterion(logits, targets)
                loss.backward()
                optimizer.step()

                running_loss += loss.item() * targets.size(0)
                preds = logits.argmax(dim=1)
                running_correct += (preds == targets).sum().item()
                running_total += targets.size(0)

            train_loss = running_loss / max(running_total, 1)
            train_acc = running_correct / max(running_total, 1)

            model.eval()
            val_loss_sum = 0.0
            val_total = 0
            val_correct = 0.0
            with torch.no_grad():
                for screens, events, targets in val_loader:
                    screens = screens.to(device)
                    events = events.to(device)
                    targets = targets.to(device)
                    logits = model(screens, events)
                    loss = criterion(logits, targets)
                    val_loss_sum += loss.item() * targets.size(0)
                    preds = logits.argmax(dim=1)
                    val_correct += (preds == targets).sum().item()
                    val_total += targets.size(0)

            val_loss = val_loss_sum / max(val_total, 1)
            val_acc = val_correct / max(val_total, 1)

            history["train_loss"].append(train_loss)
            history["val_loss"].append(val_loss)
            history["train_acc"].append(train_acc)
            history["val_acc"].append(val_acc)

            if val_acc > best_val_acc + 1e-4:
                best_val_acc = val_acc
                best_state = model.state_dict()
                no_improve = 0
            else:
                no_improve += 1
                if no_improve >= patience:
                    break

        record = {
            "config_index": idx,
            "config": cfg,
            "best_val_acc": best_val_acc,
        }
        search_records.append(record)

        if best_state is not None and best_val_acc > best_overall_acc:
            best_overall_acc = best_val_acc
            best_overall_state = best_state
            best_overall_config = cfg
            best_history = history

    if best_overall_state is None:
        raise RuntimeError("No LSTM configuration produced a valid model.")

    best_model = LSTMNextScreen(
        num_screens=num_screens,
        num_events=num_events,
        embedding_dim=best_overall_config["embedding_dim"],
        hidden_dim=best_overall_config["hidden_dim"],
        num_layers=best_overall_config["num_layers"],
        dropout=best_overall_config["dropout"],
    ).to(device)
    best_model.load_state_dict(best_overall_state)
    best_model.eval()

    test_loader = DataLoader(test_ds, batch_size=best_overall_config["batch_size"], shuffle=False)

    all_logits = []
    all_targets = []
    with torch.no_grad():
        for screens, events, targets in test_loader:
            screens = screens.to(device)
            events = events.to(device)
            targets = targets.to(device)
            logits = best_model(screens, events)
            all_logits.append(logits.cpu())
            all_targets.append(targets.cpu())

    all_logits_t = torch.cat(all_logits, dim=0)
    all_targets_t = torch.cat(all_targets, dim=0)
    acc1 = accuracy_topk(all_logits_t, all_targets_t, k=1)
    acc3 = accuracy_topk(all_logits_t, all_targets_t, k=3)

    y_test_np = np.asarray(y_test, dtype=np.int64)
    top_screens, counts = np.unique(y_test_np, return_counts=True)
    order = np.argsort(counts)[::-1]
    top10_ids = top_screens[order][:10]

    id_to_pos = {int(s): i for i, s in enumerate(top10_ids)}
    cm = np.zeros((len(top10_ids), len(top10_ids)), dtype=np.int64)

    preds1 = all_logits_t.argmax(dim=1).numpy()
    for true_id, pred_id in zip(y_test_np, preds1):
        if int(true_id) in id_to_pos and int(pred_id) in id_to_pos:
            i = id_to_pos[int(true_id)]
            j = id_to_pos[int(pred_id)]
            cm[i, j] += 1

    RESULTS_DIR.mkdir(exist_ok=True)

    epochs_range = range(1, len(best_history["train_loss"]) + 1)
    plt.figure()
    plt.plot(epochs_range, best_history["train_loss"], label="train_loss")
    plt.plot(epochs_range, best_history["val_loss"], label="val_loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "training_curves.png")
    plt.close()

    plt.figure()
    plt.imshow(cm, interpolation="nearest")
    plt.title("Confusion matrix (top 10 screens)")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.colorbar()
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "confusion_matrix.png")
    plt.close()

    val_accs = [r["best_val_acc"] for r in search_records]
    indices = [r["config_index"] for r in search_records]
    plt.figure()
    plt.bar(indices, val_accs)
    plt.xlabel("Config index")
    plt.ylabel("Best validation accuracy")
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "hyperparameter_comparison.png")
    plt.close()

    lstm_results_lines = [
        f"Best validation accuracy: {best_overall_acc:.4f}",
        f"Test top-1 accuracy: {acc1:.4f}",
        f"Test top-3 accuracy: {acc3:.4f}",
        f"Best config: {json.dumps(best_overall_config)}",
    ]
    with open(RESULTS_DIR / "lstm_results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lstm_results_lines))

    with open(RESULTS_DIR / "hyperparameter_search.txt", "w", encoding="utf-8") as f:
        for r in search_records:
            f.write(json.dumps(r) + "\n")

    checkpoint = {
        "state_dict": best_overall_state,
        "config": {
            "num_screens": num_screens,
            "num_events": num_events,
            "embedding_dim": best_overall_config["embedding_dim"],
            "hidden_dim": best_overall_config["hidden_dim"],
            "num_layers": best_overall_config["num_layers"],
            "dropout": best_overall_config["dropout"],
            "batch_size": best_overall_config["batch_size"],
            "seq_len": int(DATA_DIR.joinpath("train.pkl").stat().st_size),  # placeholder, updated below
        },
    }

    with open(DATA_DIR / "train.pkl", "rb") as f:
        train_data = pickle.load(f)
    seq_len = int(train_data["X"].shape[1])
    checkpoint["config"]["seq_len"] = seq_len

    MODELS_DIR.mkdir(exist_ok=True)
    torch.save(checkpoint, MODELS_DIR / "model_lstm.pth")


if __name__ == "__main__":
    run_training()
