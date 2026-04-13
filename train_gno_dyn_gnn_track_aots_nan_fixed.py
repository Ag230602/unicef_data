
import os
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split


@dataclass
class CFG:
    csv_path: str = r"C:\Users\Adrija\Downloads\DFGCN\AOTS_DATA_SHARE (5).csv"

    history_steps: int = 4
    lead_hours: Tuple[int, ...] = (6, 12, 24, 48)
    use_all_storms: bool = True
    selected_track_ids: Tuple[str, ...] = ()

    metadata_cols: Tuple[str, ...] = (
        "WIND_SPEED_KNOTS",
        "PRESSURE_HPA",
        "RADIUS_OF_MAXIMUM_WINDS_KM",
        "RADIUS_34_KNOT_WINDS_NE_KM",
        "RADIUS_34_KNOT_WINDS_SE_KM",
        "RADIUS_34_KNOT_WINDS_SW_KM",
        "RADIUS_34_KNOT_WINDS_NW_KM",
        "RADIUS_50_KNOT_WINDS_NE_KM",
        "RADIUS_50_KNOT_WINDS_SE_KM",
        "RADIUS_50_KNOT_WINDS_SW_KM",
        "RADIUS_50_KNOT_WINDS_NW_KM",
        "RADIUS_64_KNOT_WINDS_NE_KM",
        "RADIUS_64_KNOT_WINDS_SE_KM",
        "RADIUS_64_KNOT_WINDS_SW_KM",
        "RADIUS_64_KNOT_WINDS_NW_KM",
    )

    test_size: float = 0.25
    random_state: int = 42
    seed: int = 42
    batch_size: int = 64
    epochs: int = 25
    lr: float = 1e-4
    wd: float = 1e-4
    hidden_dim: int = 128
    dropout: float = 0.1
    grad_clip: float = 1.0
    device: str = "cuda" if torch.cuda.is_available() else "cpu"

    out_root: str = r"C:\Users\Adrija\Downloads\DFGCN_AOTS"
    ckpt_dir: str = r"C:\Users\Adrija\Downloads\DFGCN_AOTS\checkpoints"
    metrics_dir: str = r"C:\Users\Adrija\Downloads\DFGCN_AOTS\metrics"


cfg = CFG()


def seed_all(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def ensure_dirs() -> None:
    os.makedirs(cfg.ckpt_dir, exist_ok=True)
    os.makedirs(cfg.metrics_dir, exist_ok=True)


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dl = math.radians(float(lon2) - float(lon1))
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    a = min(max(a, 0.0), 1.0)
    return 2 * R * math.asin(math.sqrt(a))


def normalize_longitude(lon: pd.Series) -> pd.Series:
    lon = pd.to_numeric(lon, errors="coerce")
    if lon.dropna().empty:
        return lon
    if lon.max() > 180:
        lon = ((lon + 180) % 360) - 180
    return lon


def inverse_transform(x: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    return x * std + mean


def load_aots_tracks(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    required = {
        "FORECAST_TIME", "TRACK_ID", "ENSEMBLE_MEMBER", "VALID_TIME",
        "LEAD_TIME", "LATITUDE", "LONGITUDE", "PRESSURE_HPA", "WIND_SPEED_KNOTS"
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df["FORECAST_TIME"] = pd.to_datetime(df["FORECAST_TIME"], errors="coerce", utc=True)
    df["VALID_TIME"] = pd.to_datetime(df["VALID_TIME"], errors="coerce", utc=True)
    df["LONGITUDE"] = normalize_longitude(df["LONGITUDE"])

    numeric_cols = [
        "ENSEMBLE_MEMBER", "LEAD_TIME", "LATITUDE", "LONGITUDE",
        "PRESSURE_HPA", "WIND_SPEED_KNOTS", *cfg.metadata_cols
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    keep_cols = [
        "FORECAST_TIME", "TRACK_ID", "ENSEMBLE_MEMBER", "VALID_TIME", "LEAD_TIME",
        "LATITUDE", "LONGITUDE", "PRESSURE_HPA", "WIND_SPEED_KNOTS"
    ] + [c for c in cfg.metadata_cols if c in df.columns]
    keep_cols = list(dict.fromkeys(keep_cols))
    df = df[keep_cols].copy()
    df = df.dropna(subset=["FORECAST_TIME", "TRACK_ID", "ENSEMBLE_MEMBER", "VALID_TIME", "LATITUDE", "LONGITUDE"])
    df = df.sort_values(["TRACK_ID", "FORECAST_TIME", "ENSEMBLE_MEMBER", "VALID_TIME"]).reset_index(drop=True)

    if not cfg.use_all_storms and cfg.selected_track_ids:
        df = df[df["TRACK_ID"].isin(cfg.selected_track_ids)].copy()

    df = df.drop_duplicates(subset=["TRACK_ID", "FORECAST_TIME", "ENSEMBLE_MEMBER", "VALID_TIME"]).reset_index(drop=True)

    # Fill metadata NaNs so the network does not receive NaN inputs.
    fill_cols = [c for c in cfg.metadata_cols if c in df.columns]
    for col in fill_cols:
        median_val = df[col].median()
        if pd.isna(median_val):
            median_val = 0.0
        df[col] = df[col].fillna(median_val)

    return df


class Standardizer:
    def __init__(self):
        self.mean = None
        self.std = None

    def fit(self, x: np.ndarray) -> None:
        x = np.asarray(x, dtype=np.float32)
        self.mean = np.nanmean(x, axis=0).astype(np.float32)
        self.std = np.nanstd(x, axis=0).astype(np.float32)
        self.mean = np.where(np.isfinite(self.mean), self.mean, 0.0).astype(np.float32)
        self.std = np.where((~np.isfinite(self.std)) | (self.std < 1e-6), 1.0, self.std).astype(np.float32)

    def transform(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=np.float32)
        z = (x - self.mean) / self.std
        z = np.nan_to_num(z, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
        return z


def make_group_samples(group: pd.DataFrame) -> List[Dict]:
    group = group.sort_values("VALID_TIME").reset_index(drop=True)
    lead_steps = [h // 6 for h in cfg.lead_hours]
    if any(h % 6 != 0 for h in cfg.lead_hours):
        raise ValueError("lead_hours must be multiples of 6 for this AOTS dataset.")

    samples = []
    meta_cols = [c for c in cfg.metadata_cols if c in group.columns]

    for i in range(cfg.history_steps, len(group)):
        if i + max(lead_steps) >= len(group):
            break

        seq = group.loc[i - cfg.history_steps:i + max(lead_steps), "VALID_TIME"].reset_index(drop=True)
        diffs = seq.diff().dropna().dt.total_seconds().div(3600.0)
        if not np.allclose(diffs.values, 6.0):
            continue

        past_pos = group.loc[i - cfg.history_steps:i - 1, ["LATITUDE", "LONGITUDE"]].to_numpy(dtype=np.float32)
        past_meta = (
            group.loc[i - cfg.history_steps:i - 1, meta_cols].to_numpy(dtype=np.float32)
            if meta_cols else np.zeros((cfg.history_steps, 0), dtype=np.float32)
        )
        curr_meta = (
            group.loc[i, meta_cols].to_numpy(dtype=np.float32)
            if meta_cols else np.zeros((0,), dtype=np.float32)
        )
        future_pos = np.stack(
            [group.loc[i + step, ["LATITUDE", "LONGITUDE"]].to_numpy(dtype=np.float32) for step in lead_steps],
            axis=0,
        )

        if not np.isfinite(past_pos).all() or not np.isfinite(future_pos).all():
            continue
        if past_meta.size > 0 and not np.isfinite(past_meta).all():
            continue
        if curr_meta.size > 0 and not np.isfinite(curr_meta).all():
            continue

        samples.append({
            "track_id": str(group.loc[i, "TRACK_ID"]),
            "forecast_time": group.loc[i, "FORECAST_TIME"].isoformat(),
            "ensemble_member": int(group.loc[i, "ENSEMBLE_MEMBER"]),
            "valid_time": group.loc[i, "VALID_TIME"].isoformat(),
            "past_pos": past_pos,
            "past_meta": past_meta,
            "curr_meta": curr_meta,
            "y_abs": future_pos,
        })
    return samples


def build_samples(df: pd.DataFrame) -> List[Dict]:
    samples: List[Dict] = []
    grouped = df.groupby(["TRACK_ID", "FORECAST_TIME", "ENSEMBLE_MEMBER"], sort=False)
    for _, g in tqdm(grouped, desc="Building AOTS samples"):
        samples.extend(make_group_samples(g))
    return samples


class TrackDataset(torch.utils.data.Dataset):
    def __init__(self, samples: List[Dict]):
        self.samples = samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx: int):
        s = self.samples[idx]
        return (
            torch.from_numpy(s["past_pos"]).float(),
            torch.from_numpy(s["past_meta"]).float(),
            torch.from_numpy(s["curr_meta"]).float(),
            torch.from_numpy(s["y"]).float(),
            (s["track_id"], s["forecast_time"], s["ensemble_member"], s["valid_time"]),
        )


class PersistenceBaseline:
    def predict(self, past_pos: np.ndarray, lead_steps: List[int]) -> np.ndarray:
        p1 = past_pos[-2]
        p2 = past_pos[-1]
        v = p2 - p1
        return np.stack([p2 + v * s for s in lead_steps], axis=0).astype(np.float32)


class TemporalEncoder(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int, dropout: float):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=in_dim,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=dropout,
            bidirectional=True,
        )
        self.proj = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        return self.proj(out[:, -1, :])


class DynamicGNN(nn.Module):
    def __init__(self, node_dim: int = 64, hidden: int = 128, layers: int = 2):
        super().__init__()
        self.embed = nn.Linear(2, node_dim)
        self.layers = nn.ModuleList([
            nn.Sequential(
                nn.Linear(node_dim, hidden),
                nn.ReLU(),
                nn.Linear(hidden, node_dim),
            )
            for _ in range(layers)
        ])
        self.readout = nn.Sequential(
            nn.Linear(node_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
        )

    def forward(self, past_pos: torch.Tensor) -> torch.Tensor:
        h = self.embed(past_pos)
        d2 = ((past_pos[:, :, None, :] - past_pos[:, None, :, :]) ** 2).sum(-1)
        A = torch.softmax(-d2 / 2.0, dim=-1)
        A = torch.nan_to_num(A, nan=0.0)
        for layer in self.layers:
            m = torch.einsum("bij,bjn->bin", A, h)
            h = h + layer(m)
        return self.readout(h.mean(dim=1))


class ProbTrackHead(nn.Module):
    def __init__(self, in_dim: int, leads: int, dropout: float):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(in_dim, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        self.mu = nn.Linear(128, leads * 2)
        self.log_sigma = nn.Linear(128, leads * 2)
        self.leads = leads

    def forward(self, h: torch.Tensor):
        z = self.fc(h)
        mu = self.mu(z).view(-1, self.leads, 2)
        log_sigma = self.log_sigma(z).view(-1, self.leads, 2).clamp(-4, 2)
        sigma = torch.exp(log_sigma).clamp_min(1e-3)
        return mu, sigma


class AOTSTrackModel(nn.Module):
    def __init__(self, seq_in_dim: int, curr_meta_dim: int, hidden_dim: int, leads: int, dropout: float):
        super().__init__()
        self.temporal = TemporalEncoder(seq_in_dim, hidden_dim, dropout)
        self.gnn = DynamicGNN(node_dim=64, hidden=hidden_dim, layers=2)
        self.curr_meta_proj = nn.Sequential(
            nn.Linear(curr_meta_dim, hidden_dim),
            nn.ReLU(),
        ) if curr_meta_dim > 0 else None

        head_in = hidden_dim + hidden_dim + (hidden_dim if curr_meta_dim > 0 else 0)
        self.head = ProbTrackHead(head_in, leads, dropout)

    def forward(self, past_pos: torch.Tensor, past_meta: torch.Tensor, curr_meta: torch.Tensor):
        seq_x = torch.cat([past_pos, past_meta], dim=-1)
        h_seq = self.temporal(seq_x)
        h_gnn = self.gnn(past_pos)
        parts = [h_seq, h_gnn]
        if self.curr_meta_proj is not None:
            parts.append(self.curr_meta_proj(curr_meta))
        return self.head(torch.cat(parts, dim=-1))


def gaussian_nll(mu: torch.Tensor, sigma: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    var = (sigma ** 2).clamp_min(1e-6)
    diff2 = (y - mu) ** 2
    loss = 0.5 * (diff2 / var + torch.log(var))
    loss = torch.nan_to_num(loss, nan=1e6, posinf=1e6, neginf=1e6)
    return loss.mean()


def prepare_splits(samples: List[Dict]):
    idx = np.arange(len(samples))
    tr_idx, te_idx = train_test_split(
        idx,
        test_size=cfg.test_size,
        random_state=cfg.random_state,
        shuffle=True,
    )
    train_samples = [samples[i] for i in tr_idx]
    test_samples = [samples[i] for i in te_idx]
    return train_samples, test_samples


def standardize_samples(train_samples: List[Dict], test_samples: List[Dict]):
    pos_scaler = Standardizer()
    meta_scaler = Standardizer()

    train_pos = np.concatenate(
        [np.concatenate([s["past_pos"], s["y_abs"]], axis=0).reshape(-1, 2) for s in train_samples],
        axis=0,
    )
    pos_scaler.fit(train_pos)

    train_meta_blocks = []
    for s in train_samples:
        if s["curr_meta"].size > 0:
            train_meta_blocks.append(np.vstack([s["past_meta"], s["curr_meta"][None, :]]))
    if train_meta_blocks:
        meta_scaler.fit(np.concatenate(train_meta_blocks, axis=0))

    def _apply(samples_: List[Dict]):
        out = []
        for s in samples_:
            ns = dict(s)
            ns["past_pos"] = pos_scaler.transform(s["past_pos"])
            ns["y"] = pos_scaler.transform(s["y_abs"])
            if s["curr_meta"].size > 0:
                ns["past_meta"] = meta_scaler.transform(s["past_meta"])
                ns["curr_meta"] = meta_scaler.transform(s["curr_meta"][None, :])[0]
            else:
                ns["past_meta"] = s["past_meta"].astype(np.float32)
                ns["curr_meta"] = s["curr_meta"].astype(np.float32)
            out.append(ns)
        return out

    return _apply(train_samples), _apply(test_samples), pos_scaler, meta_scaler


@torch.no_grad()
def inverse_metrics(model, loader, pos_scaler: Standardizer) -> Dict[str, float]:
    model.eval()
    track_err = [[] for _ in cfg.lead_hours]

    for past_pos, past_meta, curr_meta, y, _ in loader:
        past_pos = past_pos.to(cfg.device)
        past_meta = past_meta.to(cfg.device)
        curr_meta = curr_meta.to(cfg.device)
        y = y.to(cfg.device)

        mu, _ = model(past_pos, past_meta, curr_meta)
        mu_np = mu.detach().cpu().numpy()
        y_np = y.detach().cpu().numpy()

        for b in range(mu_np.shape[0]):
            mu_abs = inverse_transform(mu_np[b], pos_scaler.mean, pos_scaler.std)
            y_abs = inverse_transform(y_np[b], pos_scaler.mean, pos_scaler.std)
            for li in range(mu_abs.shape[0]):
                track_err[li].append(haversine_km(y_abs[li, 0], y_abs[li, 1], mu_abs[li, 0], mu_abs[li, 1]))

    metrics = {}
    for i, h in enumerate(cfg.lead_hours):
        metrics[f"track_km_{h}h"] = float(np.mean(track_err[i])) if track_err[i] else np.nan
    metrics["mean_track_km"] = float(np.mean([metrics[f"track_km_{h}h"] for h in cfg.lead_hours]))
    return metrics


def save_checkpoint(ckpt_path: str, model, optimizer, epoch: int, best_metric: float, pos_scaler: Standardizer):
    torch.save({
        "epoch": epoch,
        "best_metric": best_metric,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict() if optimizer is not None else None,
        "cfg": cfg.__dict__,
        "pos_mean": pos_scaler.mean,
        "pos_std": pos_scaler.std,
    }, ckpt_path)


def load_checkpoint_safely(ckpt_path: str, device: str):
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")
    try:
        return torch.load(ckpt_path, map_location=device, weights_only=True)
    except Exception:
        return torch.load(ckpt_path, map_location=device, weights_only=False)


def train_main() -> None:
    ensure_dirs()
    seed_all(cfg.seed)

    print(f"Loading CSV: {cfg.csv_path}")
    df = load_aots_tracks(cfg.csv_path)
    print(f"Rows loaded: {len(df):,}")
    print(f"Unique storms: {df['TRACK_ID'].nunique()}")

    samples = build_samples(df)
    print(f"Total training samples built: {len(samples):,}")
    if len(samples) == 0:
        raise RuntimeError("No samples were created. Check time continuity and CSV content.")

    train_samples, test_samples = prepare_splits(samples)
    train_samples, test_samples, pos_scaler, _ = standardize_samples(train_samples, test_samples)

    train_ds = TrackDataset(train_samples)
    test_ds = TrackDataset(test_samples)
    train_loader = torch.utils.data.DataLoader(train_ds, batch_size=cfg.batch_size, shuffle=True)
    test_loader = torch.utils.data.DataLoader(test_ds, batch_size=cfg.batch_size, shuffle=False)

    seq_in_dim = train_samples[0]["past_pos"].shape[1] + train_samples[0]["past_meta"].shape[1]
    curr_meta_dim = train_samples[0]["curr_meta"].shape[0]

    model = AOTSTrackModel(
        seq_in_dim=seq_in_dim,
        curr_meta_dim=curr_meta_dim,
        hidden_dim=cfg.hidden_dim,
        leads=len(cfg.lead_hours),
        dropout=cfg.dropout,
    ).to(cfg.device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.wd)
    best = float("inf")
    ckpt_path = os.path.join(cfg.ckpt_dir, "aots_track_model.pt")

    for epoch in range(1, cfg.epochs + 1):
        model.train()
        losses = []
        skipped = 0

        for past_pos, past_meta, curr_meta, y, _ in tqdm(train_loader, desc=f"Epoch {epoch}/{cfg.epochs}", leave=False):
            past_pos = past_pos.to(cfg.device)
            past_meta = past_meta.to(cfg.device)
            curr_meta = curr_meta.to(cfg.device)
            y = y.to(cfg.device)

            if not (torch.isfinite(past_pos).all() and torch.isfinite(past_meta).all() and torch.isfinite(curr_meta).all() and torch.isfinite(y).all()):
                skipped += 1
                continue

            optimizer.zero_grad(set_to_none=True)
            mu, sigma = model(past_pos, past_meta, curr_meta)
            loss = gaussian_nll(mu, sigma, y)

            if not torch.isfinite(loss):
                skipped += 1
                continue

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.grad_clip)
            optimizer.step()
            losses.append(float(loss.item()))

        train_nll = float(np.mean(losses)) if losses else float("nan")
        metrics = inverse_metrics(model, test_loader, pos_scaler)
        print(f"Epoch {epoch:02d} | train_nll={train_nll:.4f} | mean_track_km={metrics['mean_track_km']:.2f} | skipped_batches={skipped}")
        print({k: round(v, 3) for k, v in metrics.items()})

        if np.isfinite(metrics["mean_track_km"]) and metrics["mean_track_km"] < best:
            best = metrics["mean_track_km"]
            save_checkpoint(ckpt_path, model, optimizer, epoch, best, pos_scaler)

    checkpoint = load_checkpoint_safely(ckpt_path, cfg.device)
    model.load_state_dict(checkpoint["model_state_dict"])
    final_metrics = inverse_metrics(model, test_loader, pos_scaler)

    pd.DataFrame([{"model": "AOTS_TrackModel", **final_metrics}]).to_csv(
        os.path.join(cfg.metrics_dir, "aots_track_metrics.csv"), index=False
    )

    lead_steps = [h // 6 for h in cfg.lead_hours]
    pers = PersistenceBaseline()
    pers_metrics = {f"track_km_{h}h": [] for h in cfg.lead_hours}

    for s in test_samples:
        past_abs = inverse_transform(s["past_pos"], pos_scaler.mean, pos_scaler.std)
        y_abs = s["y_abs"]
        preds = pers.predict(past_abs, lead_steps)
        for i, h in enumerate(cfg.lead_hours):
            pers_metrics[f"track_km_{h}h"].append(haversine_km(y_abs[i, 0], y_abs[i, 1], preds[i, 0], preds[i, 1]))

    pers_row = {k: float(np.mean(v)) for k, v in pers_metrics.items()}
    pers_row["mean_track_km"] = float(np.mean([pers_row[f"track_km_{h}h"] for h in cfg.lead_hours]))
    pd.DataFrame([{"model": "Persistence", **pers_row}]).to_csv(
        os.path.join(cfg.metrics_dir, "aots_persistence_metrics.csv"), index=False
    )

    print(f"Saved checkpoint: {ckpt_path}")
    print(f"Saved metrics to: {cfg.metrics_dir}")


if __name__ == "__main__":
    train_main()
