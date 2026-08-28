from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from api.football_data.client import FootballDataClient


def _flatten_matches(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for match in payload.get("matches", []):
        score = match.get("score", {})
        full_time = score.get("fullTime", {})
        half_time = score.get("halfTime", {})
        home_team = match.get("homeTeam", {})
        away_team = match.get("awayTeam", {})
        area = match.get("area", {})
        competition = match.get("competition", {})
        season = match.get("season", {})

        rows.append(
            {
                "match_id": match.get("id"),
                "utc_date": match.get("utcDate"),
                "status": match.get("status"),
                "matchday": match.get("matchday"),
                "stage": match.get("stage"),
                "group": match.get("group"),
                "last_updated": match.get("lastUpdated"),
                "area_name": area.get("name"),
                "competition_code": competition.get("code"),
                "competition_name": competition.get("name"),
                "season_id": season.get("id"),
                "season_start": season.get("startDate"),
                "season_end": season.get("endDate"),
                "home_team_id": home_team.get("id"),
                "home_team_name": home_team.get("name"),
                "away_team_id": away_team.get("id"),
                "away_team_name": away_team.get("name"),
                "winner": score.get("winner"),
                "duration": score.get("duration"),
                "home_score": full_time.get("home"),
                "away_score": full_time.get("away"),
                "home_score_ht": half_time.get("home"),
                "away_score_ht": half_time.get("away"),
            }
        )

    return rows


def _flatten_teams(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for team in payload.get("teams", []):
        coach = team.get("coach", {}) or {}
        area = team.get("area", {}) or {}

        rows.append(
            {
                "team_id": team.get("id"),
                "name": team.get("name"),
                "short_name": team.get("shortName"),
                "tla": team.get("tla"),
                "area_name": area.get("name"),
                "founded": team.get("founded"),
                "venue": team.get("venue"),
                "coach_name": coach.get("name"),
                "website": team.get("website"),
                "last_updated": team.get("lastUpdated"),
            }
        )

    return rows


def _write_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        output_path.write_text("", encoding="utf-8")
        return

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def ingest_competition(
    client: FootballDataClient,
    competition_code: str,
    season: int | None,
    raw_dir: Path,
    processed_dir: Path,
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
    stage: str | None = None,
) -> tuple[Path, Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    matches_payload = client.competition_matches(
        code=competition_code,
        season=season,
        date_from=date_from,
        date_to=date_to,
        status=status,
        stage=stage,
    )
    teams_payload = client.competition_teams(code=competition_code, season=season)

    season_suffix = str(season) if season is not None else "latest"
    matches_json_path = raw_dir / f"football_data_{competition_code.lower()}_{season_suffix}_matches.json"
    teams_json_path = raw_dir / f"football_data_{competition_code.lower()}_{season_suffix}_teams.json"
    matches_json_path.write_text(json.dumps(matches_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    teams_json_path.write_text(json.dumps(teams_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    matches_csv_path = processed_dir / f"football_data_{competition_code.lower()}_{season_suffix}_matches.csv"
    teams_csv_path = processed_dir / f"football_data_{competition_code.lower()}_{season_suffix}_teams.csv"
    _write_csv(_flatten_matches(matches_payload), matches_csv_path)
    _write_csv(_flatten_teams(teams_payload), teams_csv_path)
    return matches_csv_path, teams_csv_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest free-tier data from football-data.org.")
    parser.add_argument(
        "--competition",
        required=True,
        action="append",
        help="Competition code like WC, PL, BSA, CL, EC. Repeat the flag to ingest multiple competitions.",
    )
    parser.add_argument("--season", type=int, default=None, help="Season year accepted by the API.")
    parser.add_argument("--date-from", default=None, help="Filter matches from date YYYY-MM-DD.")
    parser.add_argument("--date-to", default=None, help="Filter matches until date YYYY-MM-DD.")
    parser.add_argument("--status", default=None, help="Optional match status filter, e.g. FINISHED.")
    parser.add_argument("--stage", default=None, help="Optional stage filter, e.g. GROUP_STAGE.")
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--processed-dir", default="data/processed")
    args = parser.parse_args()

    client = FootballDataClient()
    for competition_code in args.competition:
        matches_path, teams_path = ingest_competition(
            client=client,
            competition_code=competition_code,
            season=args.season,
            raw_dir=Path(args.raw_dir),
            processed_dir=Path(args.processed_dir),
            date_from=args.date_from,
            date_to=args.date_to,
            status=args.status,
            stage=args.stage,
        )
        print(f"Wrote {matches_path}")
        print(f"Wrote {teams_path}")


if __name__ == "__main__":
    main()
