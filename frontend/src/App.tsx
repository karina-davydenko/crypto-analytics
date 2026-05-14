import { useState } from "react";
import { CoinDetail } from "./components/CoinDetail";
import { CoinsTable } from "./components/CoinsTable";
import { PeriodFilter } from "./components/PeriodFilter";
import type { CoinSummary, Period } from "./types";

export default function App() {
  const [period, setPeriod] = useState<Period>("7d");
  const [selectedCoin, setSelectedCoin] = useState<CoinSummary | null>(null);

  function handleSelect(coin: CoinSummary) {
    setSelectedCoin((prev) => (prev?.coin_id === coin.coin_id ? null : coin));
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        flex: 1,
        minHeight: 0,
        gap: 16,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexShrink: 0,
        }}
      >
        <div>
          <h1>Crypto Analytics</h1>
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Топ монеты · обновляется каждый час
          </span>
        </div>
        <PeriodFilter value={period} onChange={setPeriod} />
      </div>

      <div style={{ display: "flex", flex: 1, minHeight: 0, gap: 16 }}>
        <div
          style={{
            flex: selectedCoin ? "0 0 52%" : "1",
            display: "flex",
            flexDirection: "column",
            minWidth: 0,
            minHeight: 0,
          }}
        >
          <CoinsTable
            selectedCoinId={selectedCoin?.coin_id ?? null}
            onSelect={handleSelect}
          />
        </div>

        {selectedCoin && (
          <div style={{ flex: 1, minWidth: 0, overflowY: "auto" }}>
            <CoinDetail
              coinId={selectedCoin.coin_id}
              coinName={selectedCoin.coin_name}
              currentPrice={selectedCoin.close_price}
              currentChange={selectedCoin.daily_change_pct}
              period={period}
            />
          </div>
        )}
      </div>
    </div>
  );
}
