from datetime import datetime, timedelta, timezone
from pathlib import Path

from alpaca.data.enums import Adjustment, DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame


def read_env(path: Path) -> dict[str, str]:
    values = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key, value = stripped.split("=", 1)
                values[key.strip()] = value.strip().strip("\"'")
    return values


def main() -> None:
    credentials = read_env(Path(".env"))
    api_key = credentials.get("ALPACA_API_KEY", "")
    secret_key = credentials.get("ALPACA_SECRET_KEY", "")
    if not api_key or not secret_key:
        raise SystemExit(
            "Faltan ALPACA_API_KEY o ALPACA_SECRET_KEY en el archivo .env "
            "de la carpeta principal del proyecto."
        )

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=5 * 365)
    request = StockBarsRequest(
        symbol_or_symbols="QQQ",
        timeframe=TimeFrame.Hour,
        start=start,
        end=end,
        adjustment=Adjustment.ALL,
        feed=DataFeed.IEX,
    )
    client = StockHistoricalDataClient(api_key, secret_key)
    bars = client.get_stock_bars(request).df
    if bars.empty:
        raise SystemExit("Alpaca no devolvió velas para QQQ en el período solicitado.")

    output = Path("datos/crudos/qqq_1h_alpaca.csv")
    output.parent.mkdir(parents=True, exist_ok=True)
    bars.reset_index().to_csv(output, index=False)
    print(f"Crudo guardado: {output} ({len(bars)} velas)")


if __name__ == "__main__":
    main()
