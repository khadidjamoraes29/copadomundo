from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from api.transfermarkt.client import TransfermarktClient
from api.transfermarkt.transform import build_team_features, normalize_squad_payload


DEFAULT_TEAMS = [
    "Argentina",
    "Brazil",
    "England",
    "France",
    "Germany",
    "Netherlands",
    "Portugal",
    "Spain",
]


def load_team_map(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return [{"team": team, "club_id": team} for team in DEFAULT_TEAMS]
    return json.loads(path.read_text(encoding="utf-8"))


def ingest_squads(
    season_id: str,
    team_map_path: Path,
    raw_dir: Path,
    processed_dir: Path,
) -> tuple[Path, Path]:
    client = TransfermarktClient()
    team_map = load_team_map(team_map_path)
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    squads = []
    for item in team_map:
        team = item["team"]
        club_id = item.get("club_id") or item["team"]
        payload = client.club_squad(str(club_id), season_id)

        raw_path = raw_dir / f"transfermarkt_{team.lower().replace(' ', '_')}_{season_id}.json"
        raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        squads.append(normalize_squad_payload(payload, team=team, season_id=season_id))

    players = pd.concat(squads, ignore_index=True)
    features = build_team_features(players)

    players_path = processed_dir / f"transfermarkt_players_{season_id}.csv"
    features_path = processed_dir / f"transfermarkt_team_features_{season_id}.csv"
    players.to_csv(players_path, index=False)
    features.to_csv(features_path, index=False)
    return players_path, features_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Transfermarkt squad data.")
    parser.add_argument("--season-id", required=True, help="Season identifier expected by the API.")
    parser.add_argument("--team-map", default="data/transfermarkt_teams.json")
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--processed-dir", default="data/processed")
    args = parser.parse_args()

    players_path, features_path = ingest_squads(
        season_id=args.season_id,
        team_map_path=Path(args.team_map),
        raw_dir=Path(args.raw_dir),
        processed_dir=Path(args.processed_dir),
    )
    print(f"Wrote {players_path}")
    print(f"Wrote {features_path}")


if __name__ == "__main__":
    main()

