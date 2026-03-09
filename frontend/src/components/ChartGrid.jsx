import { useState } from "react";
import {
  Chart as ChartJS,
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar, Doughnut } from "react-chartjs-2";

ChartJS.register(
  ArcElement,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
);

const MULTI_COLORS = [
  "#2196F3", "#4CAF50", "#FF9800", "#F44336",
  "#9C27B0", "#00BCD4", "#FF5722", "#607D8B",
];

const tooltipStyle = {
  backgroundColor: "#1e293b",
  titleColor: "#e5e7eb",
  bodyColor: "#94a3b8",
  borderColor: "#334155",
  borderWidth: 1,
  padding: 10,
};

const darkScales = {
  x: {
    ticks: { color: "#9ca3af", font: { size: 11 } },
    grid: { color: "#1f2937" },
  },
  y: {
    ticks: { color: "#9ca3af", font: { size: 11 } },
    grid: { color: "#1f2937" },
  },
};

const horizontalBarOptions = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: "y",
  plugins: {
    legend: { display: false },
    tooltip: tooltipStyle,
  },
  scales: darkScales,
};

const verticalBarOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: tooltipStyle,
  },
  scales: darkScales,
};

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: "62%",
  plugins: {
    legend: {
      position: "bottom",
      labels: { color: "#e5e7eb", padding: 16, font: { size: 12 } },
    },
    tooltip: tooltipStyle,
  },
};

const TOP_N = 10;

export default function ChartGrid({ chartData }) {
  const [showAllCategories, setShowAllCategories] = useState(false);

  if (!chartData) return null;

  const facilityData = {
    labels: Object.keys(chartData.by_facility),
    datasets: [
      {
        label: "Observations",
        data: Object.values(chartData.by_facility),
        backgroundColor: "#2196F3",
        borderRadius: 4,
      },
    ],
  };

  // Sort categories descending by count, take top 10
  const allCategoryEntries = Object.entries(chartData.by_category).sort(
    (a, b) => b[1] - a[1]
  );
  const hasMoreCategories = allCategoryEntries.length > TOP_N;
  const topCategoryEntries = hasMoreCategories
    ? allCategoryEntries.slice(0, TOP_N)
    : allCategoryEntries;

  const categoryData = {
    labels: topCategoryEntries.map(([k]) => k),
    datasets: [
      {
        label: "Observations",
        data: topCategoryEntries.map(([, v]) => v),
        backgroundColor: topCategoryEntries.map(
          (_, i) => MULTI_COLORS[i % MULTI_COLORS.length]
        ),
        borderRadius: 4,
      },
    ],
  };

  const fullCategoryData = hasMoreCategories
    ? {
        labels: allCategoryEntries.map(([k]) => k),
        datasets: [
          {
            label: "Observations",
            data: allCategoryEntries.map(([, v]) => v),
            backgroundColor: allCategoryEntries.map(
              (_, i) => MULTI_COLORS[i % MULTI_COLORS.length]
            ),
            borderRadius: 4,
          },
        ],
      }
    : null;

  const safeRiskData = {
    labels: ["Safe", "At Risk"],
    datasets: [
      {
        data: [
          chartData.safe_vs_atrisk?.Safe ?? 0,
          chartData.safe_vs_atrisk?.["At Risk"] ?? 0,
        ],
        backgroundColor: ["#4CAF50", "#F44336"],
        borderColor: "#0f172a",
        borderWidth: 3,
      },
    ],
  };

  const atRiskData = {
    labels: Object.keys(chartData.top_atrisk_categories),
    datasets: [
      {
        label: "At-Risk Count",
        data: Object.values(chartData.top_atrisk_categories),
        backgroundColor: "#F44336",
        borderRadius: 4,
      },
    ],
  };

  // Interventions by Facility (5th chart) — sorted high-to-low
  const interventionsFacility = chartData.interventions_by_facility || {};
  const interventionEntries = Object.entries(interventionsFacility).sort(
    (a, b) => b[1] - a[1]
  );
  const hasInterventions = interventionEntries.length > 0;

  const interventionsData = hasInterventions
    ? {
        labels: interventionEntries.map(([k]) => k),
        datasets: [
          {
            label: "Interventions",
            data: interventionEntries.map(([, v]) => v),
            backgroundColor: "#9C27B0",
            borderRadius: 4,
          },
        ],
      }
    : null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <ChartCard title="Observations by Facility">
        <Bar data={facilityData} options={horizontalBarOptions} />
      </ChartCard>

      <ChartCard title={hasMoreCategories ? "Top 10 Categories" : "Observations by Category"}>
        <Bar data={categoryData} options={horizontalBarOptions} />
      </ChartCard>

      <ChartCard title="At-Risk vs Safe" height={280}>
        <Doughnut data={safeRiskData} options={doughnutOptions} />
      </ChartCard>

      <ChartCard title="Top At-Risk Categories">
        <Bar data={atRiskData} options={verticalBarOptions} />
      </ChartCard>

      {hasInterventions && (
        <ChartCard title="Interventions by Facility" colSpan>
          <Bar data={interventionsData} options={verticalBarOptions} />
        </ChartCard>
      )}

      {hasMoreCategories && (
        <div className="md:col-span-2">
          <button
            onClick={() => setShowAllCategories((v) => !v)}
            className="text-sm text-blue-400 hover:text-blue-300 mb-3 transition-colors"
          >
            {showAllCategories ? "Hide all categories" : `Show all ${allCategoryEntries.length} categories`}
          </button>
          {showAllCategories && (
            <ChartCard title="All Categories" height={Math.max(320, allCategoryEntries.length * 28)}>
              <Bar data={fullCategoryData} options={horizontalBarOptions} />
            </ChartCard>
          )}
        </div>
      )}
    </div>
  );
}

function ChartCard({ title, children, height = 320, colSpan = false }) {
  return (
    <div className={`bg-gray-900 rounded-xl border border-gray-800 p-5${colSpan ? " md:col-span-2" : ""}`}>
      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-4">
        {title}
      </h3>
      <div style={{ height }}>
        {children}
      </div>
    </div>
  );
}
