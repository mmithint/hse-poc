import { useState } from "react";
import ChartGrid from "./ChartGrid";
import SummaryPanel from "./SummaryPanel";
import EmailModal from "./EmailModal";
import ComparisonView from "./ComparisonView";
import { downloadReport } from "../api/client";

export default function Dashboard({
  chartData,
  userSummary,
  managerSummary,
  detailedSummary,
  categoryAnalysis,
  dateRange,
  totalObservations,
  uploadId,
  history,
}) {
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [selectedUploadIds, setSelectedUploadIds] = useState([]);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const blob = await downloadReport({
        upload_id: uploadId,
        user_summary: userSummary,
        total_observations: totalObservations,
        manager_summary: managerSummary || "",
        detailed_summary: detailedSummary || "",
        category_analysis: categoryAnalysis || [],
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `HSE_Report_${dateRange.replace(/\s/g, "_")}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.response?.data?.detail ?? "PDF download failed. Please try again.");
    } finally {
      setDownloading(false);
    }
  };

  const safeCount = chartData?.safe_vs_atrisk?.Safe ?? 0;
  const atRiskCount = chartData?.safe_vs_atrisk?.["At Risk"] ?? 0;
  const atRiskPct =
    totalObservations > 0
      ? ((atRiskCount / totalObservations) * 100).toFixed(1)
      : "0.0";
  const interventionCount = chartData?.total_interventions ?? 0;

  // Filter history to exclude the current upload from the comparison list
  const historyForComparison = (history || []).filter(
    (h) => h.upload_id !== uploadId
  );

  const toggleCompareUpload = (id) => {
    setSelectedUploadIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 3) return prev; // max 3 others + current = 4 total
      return [...prev, id];
    });
  };

  // Build the full list: current + selected, for multi-compare
  const compareUploadIds =
    selectedUploadIds.length > 0 ? [uploadId, ...selectedUploadIds] : [];

  return (
    <div className="space-y-7">
      {/* KPI strip */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <KPICard label="Total Observations" value={totalObservations?.toLocaleString()} color="blue" />
        <KPICard label="Safe Observations" value={safeCount?.toLocaleString()} color="green" />
        <KPICard label="At-Risk Observations" value={atRiskCount?.toLocaleString()} color="red" />
        <KPICard label="At-Risk Rate" value={`${atRiskPct}%`} color="orange" />
        <KPICard label="Interventions" value={interventionCount?.toLocaleString()} color="purple" />
      </div>

      {/* Charts */}
      <ChartGrid chartData={chartData} />

      {/* AI summary with tabs */}
      <SummaryPanel
        userSummary={userSummary}
        managerSummary={managerSummary}
        detailedSummary={detailedSummary}
        categoryAnalysis={categoryAnalysis}
        dateRange={dateRange}
        onSendEmail={() => setShowEmailModal(true)}
        onDownload={handleDownload}
        downloading={downloading}
      />

      {/* Week-over-Week comparison */}
      {historyForComparison.length > 0 && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
          <div className="mb-4">
            <h2 className="text-base font-semibold text-white">
              Week-over-Week Comparison
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Select up to 3 previous uploads to compare trends (max 4 weeks total)
            </p>
          </div>

          <div className="flex flex-wrap gap-3 mb-4">
            {historyForComparison.map((h) => {
              const checked = selectedUploadIds.includes(h.upload_id);
              const disabled = !checked && selectedUploadIds.length >= 3;
              return (
                <label
                  key={h.upload_id}
                  className={[
                    "flex items-center gap-2 px-3 py-2 rounded-lg border text-sm cursor-pointer transition-colors",
                    checked
                      ? "bg-blue-900/40 border-blue-600 text-blue-300"
                      : disabled
                      ? "bg-gray-800/40 border-gray-700 text-gray-600 cursor-not-allowed"
                      : "bg-gray-800 border-gray-600 text-gray-300 hover:border-gray-500",
                  ].join(" ")}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    disabled={disabled}
                    onChange={() => toggleCompareUpload(h.upload_id)}
                    className="accent-blue-500"
                  />
                  <span>{h.date_range} — {h.filename}</span>
                </label>
              );
            })}
          </div>

          {compareUploadIds.length >= 2 ? (
            <ComparisonView uploadIds={compareUploadIds} />
          ) : (
            <div className="border border-dashed border-gray-700 rounded-lg p-8 text-center">
              <p className="text-gray-500 text-sm">
                Select at least one previous upload above to compare metrics and trends
              </p>
            </div>
          )}
        </div>
      )}

      {showEmailModal && (
        <EmailModal
          managerSummary={managerSummary}
          uploadId={uploadId}
          dateRange={dateRange}
          onClose={() => setShowEmailModal(false)}
        />
      )}
    </div>
  );
}

function KPICard({ label, value, color }) {
  const styles = {
    blue: "bg-blue-950/50 border-blue-800/60",
    green: "bg-green-950/50 border-green-800/60",
    red: "bg-red-950/50 border-red-800/60",
    orange: "bg-orange-950/50 border-orange-800/60",
    purple: "bg-purple-950/50 border-purple-800/60",
  };
  const valueColors = {
    blue: "text-blue-300",
    green: "text-green-300",
    red: "text-red-300",
    orange: "text-orange-300",
    purple: "text-purple-300",
  };
  return (
    <div className={`rounded-xl border p-5 ${styles[color]}`}>
      <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">{label}</p>
      <p className={`text-3xl font-bold ${valueColors[color]}`}>{value}</p>
    </div>
  );
}
