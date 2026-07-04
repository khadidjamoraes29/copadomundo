from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def add_transfermarkt_features(
    matches_path: Path,
    transfermarkt_features_path: Path,
    output_path: Path,
) -> Path:
    matches = pd.read_csv(matches_path)
    tm_features = pd.read_csv(transfermarkt_features_path)

    rename_map = {
        column: f"transfermarkt_{column}"
        for column in tm_features.columns
        if column != "team" and not column.startswith("transfermarkt_")
    }
    tm_features = tm_features.rename(columns=rename_map)

    home_features = tm_features.add_prefix("home_").rename(columns={"home_team": "home_team"})
    away_features = tm_features.add_prefix("away_").rename(columns={"away_team": "away_team"})

    dataset = matches.merge(home_features, on="home_team", how="left")
    dataset = dataset.merge(away_features, on="away_team", how="left")

    pairs = [
        "squad_value_eur",
        "avg_market_value_eur",
        "median_market_value_eur",
        "avg_age",
        "value_attack",
        "value_midfield",
        "value_defense",
        "value_goalkeeper",
        "power_score",
    ]
    for feature in pairs:
        home_col = f"home_transfermarkt_{feature}"
        away_col = f"away_transfermarkt_{feature}"
        if home_col in dataset and away_col in dataset:
            dataset[f"transfermarkt_{feature}_difference"] = dataset[home_col] - dataset[away_col]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(output_path, index=False)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge Transfermarkt features into match dataset.")
    parser.add_argument("--matches", default="data/final_matches_with_form.csv")
    parser.add_argument("--features", required=True)
    parser.add_argument("--output", default="data/final_matches_with_transfermarkt.csv")
    args = parser.parse_args()

    output_path = add_transfermarkt_features(
        matches_path=Path(args.matches),
        transfermarkt_features_path=Path(args.features),
        output_path=Path(args.output),
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
