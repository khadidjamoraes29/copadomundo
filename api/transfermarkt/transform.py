from __future__ import annotations

import math
from typing import Any

import pandas as pd


POSITION_GROUPS = {
    "Goalkeeper": "goalkeeper",
    "Defender": "defense",
    "Centre-Back": "defense",
    "Left-Back": "defense",
    "Right-Back": "defense",
    "Midfielder": "midfield",
    "Defensive Midfield": "midfield",
    "Central Midfield": "midfield",
    "Attacking Midfield": "midfield",
    "Forward": "attack",
    "Centre-Forward": "attack",
    "Left Winger": "attack",
    "Right Winger": "attack",
    "Second Striker": "attack",
}


def parse_market_value(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().replace("€", "").replace(",", ".")
    if not text or text == "-":
        return None

    multiplier = 1.0
    lowered = text.lower()
    if "bn" in lowered or "b" in lowered:
        multiplier = 1_000_000_000
    elif "m" in lowered:
        multiplier = 1_000_000
    elif "k" in lowered:
        multiplier = 1_000

    numeric = "".join(char for char in text if char.isdigit() or char == ".")
    return float(numeric) * multiplier if numeric else None


def normalize_squad_payload(payload: Any, team: str, season_id: str | int) -> pd.DataFrame:
    players = payload.get("players", payload) if isinstance(payload, dict) else payload
    rows: list[dict[str, Any]] = []

    for player in players:
        position = player.get("position") or player.get("mainPosition") or player.get("positionName")
        rows.append(
            {
                "team": team,
                "season_id": season_id,
                "player_id": player.get("id") or player.get("player_id"),
                "player_name": player.get("name") or player.get("playerName"),
                "age": player.get("age"),
                "position": position,
                "position_group": POSITION_GROUPS.get(position, "other"),
                "nationality": player.get("nationality") or player.get("country"),
                "market_value_eur": parse_market_value(
                    player.get("marketValue")
                    or player.get("market_value")
                    or player.get("marketValueAmount")
                ),
            }
        )

    return pd.DataFrame(rows)


def build_team_features(players: pd.DataFrame) -> pd.DataFrame:
    df = players.copy()
    df["market_value_eur"] = pd.to_numeric(df["market_value_eur"], errors="coerce")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")

    base = (
        df.groupby("team", as_index=False)
        .agg(
            squad_size=("player_name", "count"),
            squad_value_eur=("market_value_eur", "sum"),
            avg_market_value_eur=("market_value_eur", "mean"),
            median_market_value_eur=("market_value_eur", "median"),
            avg_age=("age", "mean"),
        )
        .fillna(0)
    )

    by_position = (
        df.pivot_table(
            index="team",
            columns="position_group",
            values="market_value_eur",
            aggfunc="sum",
            fill_value=0,
        )
        .add_prefix("value_")
        .reset_index()
    )

    features = base.merge(by_position, on="team", how="left").fillna(0)
    for column in ["value_attack", "value_midfield", "value_defense", "value_goalkeeper"]:
        if column not in features:
            features[column] = 0.0

    features["transfermarkt_power_score"] = (
        features["squad_value_eur"].rank(pct=True) * 70
        + features["avg_market_value_eur"].rank(pct=True) * 30
    )
    return features

