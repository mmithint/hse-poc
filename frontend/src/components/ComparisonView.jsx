import { useState, useEffect } from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
} from "chart.js";
import { compareUploads } from "../api/client";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip);

export default function ComparisonView({ currentUploadId, previousUploadId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!previousUploadId) return;
    setLoading(true);
    setError(null);
    setData(null);
    compareUploads(currentUploadId, previousUploadId)
      .then(setData)
      .catch((err) =>
        setError(err.response?.data?.detail ?? "Comparison failed. Please try again.")
      )
      .finally(() => setLoading(false));
  }, [currentUploadId, previousUploadId]);

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

  return (
    <div className="space-y-6">
      {/* Period labels */}
      <div className="flex items-center gap-3 text-sm flex-wrap">
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block" />
          <span className="text-blue-300 font-medium">Current: {data.current_date_range}</span>
        </span>
        <span className="text-gray-600">vs</span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-gray-500 inline-block" />
          <span className="text-gray-400">Previous: {data.previous_date_range}</span>
        </span>
      </div>

      {/* Delta cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {data.delta_cards.map((card) => (
          <DeltaCard key={card.label} card={card} />
        ))}
      </div>

      {/* Side-by-side charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SideBySideChart
          title="By Facility"
          current={{ data: data.current_chart_data.by_facility, label: data.current_date_range }}
          previous={{ data: data.previous_chart_data.by_facility, label: data.previous_date_range }}
        />
        <SideBySideChart
          title="By Category"
          current={{ data: data.current_chart_data.by_category, label: data.current_date_range }}
          previous={{ data: data.previous_chart_data.by_category, label: data.previous_date_range }}
        />
      </div>
    </div>
  );
}

function DeltaCard({ card }) {
  const isUp = card.delta > 0;
  const isNeutral = card.delta === 0;

  // Semantic coloring: for "At-Risk %", up is bad; for everything else, up is good
  const isGood = isNeutral
    ? null
    : card.good_direction === "up" ? isUp : !isUp;

  const arrowIcon = isNeutral ? "—" : isUp ? "▲" : "▼";
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
        {arrowIcon} {Math.abs(card.delta_pct).toFixed(1)}% vs previous
      </p>
      <p className="text-xs text-gray-500 mt-1">
        Previous: {formatVal(card.previous)}
      </p>
    </div>
  );
}

function SideBySideChart({ title, current, previous }) {
  // Merge keys from both datasets
  const allKeys = [
    ...new Set([
      ...Object.keys(current.data),
      ...Object.keys(previous.data),
    ]),
  ];

  const chartData = {
    labels: allKeys,
    datasets: [
      {
        label: current.label,
        data: allKeys.map((k) => current.data[k] ?? 0),
        backgroundColor: "rgba(59,130,246,0.75)",
        borderRadius: 3,
      },
      {
        label: previous.label,
        data: allKeys.map((k) => previous.data[k] ?? 0),
        backgroundColor: "rgba(100,116,139,0.55)",
        borderRadius: 3,
      },
    ],
  };

  const options = {
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

  const height = Math.max(160, allKeys.length * 36);

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
      <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
        {title}
      </h4>
      <div style={{ height }}>
        <Bar data={chartData} options={options} />
      </div>
    </div>
  );
}
