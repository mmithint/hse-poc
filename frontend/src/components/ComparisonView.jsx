import { useState, useEffect } from "react";
import { Bar, Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Tooltip,
  Legend,
} from "chart.js";
import { multiCompare, downloadComparison } from "../api/client";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Tooltip,
  Legend
);

export default function ComparisonView({ uploadIds }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  useEffect(() => {
    if (!uploadIds || uploadIds.length < 2) return;
    setLoading(true);
    setError(null);
    setData(null);
    multiCompare(uploadIds)
      .then(setData)
      .catch((err) =>
        setError(err.response?.data?.detail ?? "Comparison failed. Please try again.")
      )
      .finally(() => setLoading(false));
  }, [JSON.stringify(uploadIds)]);

  const handleDownloadComparison = async () => {
    setDownloadingPdf(true);
    try {
      const blob = await downloadComparison(uploadIds);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "HSE_Comparison.pdf";
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.response?.data?.detail ?? "PDF download failed. Please try again.");
    } finally {
      setDownloadingPdf(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center gap-3 py-6 text-gray-400 text-sm">
        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10"
            stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
        </svg>
        Loading comparison...
      </div>
    );
  }

  if (error) {
    return (
      <p className="text-red-400 text-sm bg-red-900/20 border border-red-800
                    rounded-lg px-4 py-3">
        {error}
      </p>
    );
  }

  if (!data) return null;

  const weekColors = [
    "rgba(59,130,246,0.85)",
    "rgba(16,185,129,0.85)",
    "rgba(245,158,11,0.85)",
    "rgba(239,68,68,0.85)",
  ];
  const weekBorders = [
    "rgb(59,130,246)",
    "rgb(16,185,129)",
    "rgb(245,158,11)",
    "rgb(239,68,68)",
  ];

  // Trend line charts
  const trendLineOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "#1e293b",
        titleColor: "#e5e7eb",
        bodyColor: "#94a3b8",
        borderColor: "#334155",
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        ticks: { color: "#9ca3af", font: { size: 10 } },
        grid: { color: "#1f2937" },
      },
      y: {
        ticks: { color: "#9ca3af", font: { size: 11 } },
        grid: { color: "#1f2937" },
      },
    },
  };

  const makeTrendData = (key, label, color) => ({
    labels: data.trend_labels,
    datasets: [
      {
        label,
        data: data.trends[key],
        borderColor: color,
        backgroundColor: color.replace(")", ",0.1)").replace("rgb", "rgba"),
        fill: true,
        tension: 0.3,
        pointRadius: 5,
        pointBackgroundColor: color,
      },
    ],
  });

  // Grouped facility bar chart
  const allFacilities = [
    ...new Set(data.weeks.flatMap((w) => Object.keys(w.chart_data.by_facility))),
  ];
  const facilityChartData = {
    labels: allFacilities,
    datasets: data.weeks.map((w, i) => ({
      label: w.date_range,
      data: allFacilities.map((f) => w.chart_data.by_facility[f] ?? 0),
      backgroundColor: weekColors[i],
      borderRadius: 3,
    })),
  };

  const facilityOptions = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: "y",
    plugins: {
      legend: {
        display: true,
        position: "top",
        labels: { color: "#9ca3af", boxWidth: 12, font: { size: 11 } },
      },
      tooltip: { mode: "index" },
    },
    scales: {
      x: {
        ticks: { color: "#6b7280", font: { size: 11 } },
        grid: { color: "#1f2937" },
      },
      y: {
        ticks: { color: "#9ca3af", font: { size: 11 } },
        grid: { color: "#1f2937" },
      },
    },
  };

  const facilityHeight = Math.max(180, allFacilities.length * 40);

  return (
    <div className="space-y-6">
      {/* Week labels */}
      <div className="flex items-center gap-3 text-sm flex-wrap">
        {data.weeks.map((w, i) => (
          <span key={w.upload_id} className="flex items-center gap-1.5">
            <span
              className="w-2.5 h-2.5 rounded-full inline-block"
              style={{ backgroundColor: weekBorders[i] }}
            />
            <span style={{ color: weekBorders[i] }} className="font-medium">
              {w.date_range}
            </span>
          </span>
        ))}
      </div>

      {/* Download button */}
      <button
        onClick={handleDownloadComparison}
        disabled={downloadingPdf}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
                   bg-gray-700 text-gray-200 hover:bg-gray-600 disabled:opacity-50
                   disabled:cursor-not-allowed transition-colors"
      >
        {downloadingPdf ? (
          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10"
              stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
          </svg>
        ) : (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5 5-5M12 15V3" />
          </svg>
        )}
        {downloadingPdf ? "Generating…" : "Download Comparison PDF"}
      </button>

      {/* Delta cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {data.delta_cards.map((card) => (
          <DeltaCard key={card.label} card={card} />
        ))}
      </div>

      {/* Trend line charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <TrendCard title="Total Observations Trend">
          <Line
            data={makeTrendData("total_observations", "Total Observations", "rgb(59,130,246)")}
            options={trendLineOptions}
          />
        </TrendCard>
        <TrendCard title="Safe % Trend">
          <Line
            data={makeTrendData("safe_pct", "Safe %", "rgb(16,185,129)")}
            options={trendLineOptions}
          />
        </TrendCard>
        <TrendCard title="At-Risk % Trend">
          <Line
            data={makeTrendData("atrisk_pct", "At-Risk %", "rgb(239,68,68)")}
            options={trendLineOptions}
          />
        </TrendCard>
        <TrendCard title="Interventions Trend">
          <Line
            data={makeTrendData("interventions", "Interventions", "rgb(168,85,247)")}
            options={trendLineOptions}
          />
        </TrendCard>
      </div>

      {/* Grouped facility bar chart */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
          By Facility (All Weeks)
        </h4>
        <div style={{ height: facilityHeight }}>
          <Bar data={facilityChartData} options={facilityOptions} />
        </div>
      </div>

      {/* Cross-week evolution narrative */}
      {data.trend_narrative && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 space-y-4">
          <h3 className="text-sm font-semibold text-white uppercase tracking-wide">
            Cross-Week Evolution
          </h3>

          {data.trend_narrative.overall_narrative && (
            <div className="bg-blue-950/40 border border-blue-800/40 rounded-lg p-4">
              <p className="text-sm text-gray-200 leading-relaxed">
                {data.trend_narrative.overall_narrative}
              </p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Improvements */}
            {data.trend_narrative.improvements?.length > 0 && (
              <div>
                <p className="text-xs text-green-400 uppercase tracking-wide font-medium mb-2">
                  Improvements
                </p>
                <ul className="space-y-2">
                  {data.trend_narrative.improvements.map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-200">
                      <span className="text-green-400 mt-0.5 flex-shrink-0">&#x25B2;</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Persistent Risks */}
            {data.trend_narrative.persistent_risks?.length > 0 && (
              <div>
                <p className="text-xs text-red-400 uppercase tracking-wide font-medium mb-2">
                  Persistent Risks
                </p>
                <ul className="space-y-2">
                  {data.trend_narrative.persistent_risks.map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-200">
                      <span className="text-red-400 mt-0.5 flex-shrink-0">&#x26A0;</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function DeltaCard({ card }) {
  const isUp = card.delta > 0;
  const isNeutral = card.delta === 0;
  const isGood = isNeutral
    ? null
    : card.good_direction === "up" ? isUp : !isUp;

  const arrowIcon = isNeutral ? "\u2014" : isUp ? "\u25B2" : "\u25BC";
  const deltaColor = isNeutral
    ? "text-gray-400"
    : isGood
    ? "text-green-400"
    : "text-red-400";

  const formatVal = (v) =>
    typeof v === "number" && v % 1 !== 0
      ? `${v.toFixed(1)}%`
      : v.toLocaleString();

  return (
    <div className="bg-gray-800/50 rounded-xl border border-gray-700 p-4">
      <p className="text-xs text-gray-400 uppercase tracking-wide mb-2 font-medium">
        {card.label}
      </p>
      <p className="text-2xl font-bold text-white mb-1">{formatVal(card.current)}</p>
      <p className={`text-sm font-medium ${deltaColor}`}>
        {arrowIcon} {Math.abs(card.delta_pct).toFixed(1)}% vs first week
      </p>
      <p className="text-xs text-gray-500 mt-1">
        First week: {formatVal(card.previous)}
      </p>
    </div>
  );
}

function TrendCard({ title, children }) {
  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
      <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
        {title}
      </h4>
      <div style={{ height: 200 }}>
        {children}
      </div>
    </div>
  );
}
