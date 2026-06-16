import json
from pathlib import Path


class Storage:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.reports_dir = self.base_dir / "reports"
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        for d in [self.reports_dir, self.data_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def save_report_json(self, date: str, report: dict) -> Path:
        path = self.reports_dir / f"{date}.json"
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return path

    def save_report_html(self, date: str, html: str) -> Path:
        path = self.reports_dir / f"{date}.html"
        path.write_text(html, encoding="utf-8")
        return path

    def load_report(self, date: str) -> dict | None:
        path = self.reports_dir / f"{date}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def load_latest_report(self) -> dict | None:
        reports = sorted(self.reports_dir.glob("*.json"))
        if not reports:
            return None
        return json.loads(reports[-1].read_text(encoding="utf-8"))

    def list_report_dates(self) -> list[str]:
        return sorted([p.stem for p in self.reports_dir.glob("*.json")], reverse=True)

    def load_watchlist(self) -> list[str]:
        path = self.data_dir / "watchlist.json"
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def save_watchlist(self, tickers: list[str]) -> None:
        path = self.data_dir / "watchlist.json"
        path.write_text(json.dumps(sorted(set(tickers)), indent=2), encoding="utf-8")

    def load_user_profile(self) -> dict:
        path = self.data_dir / "user_profile.json"
        if not path.exists():
            return {"halal_filter": False}
        return json.loads(path.read_text(encoding="utf-8"))
