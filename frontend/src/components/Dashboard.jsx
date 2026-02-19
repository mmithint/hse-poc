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
  dateRange,
  totalObservations,
  uploadId,
  history,
}) {
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [compareUploadId, setCompareUploadId] = useState("");

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const blob = await downloadReport({
        upload_id: uploadId,
        user_summary: userSummary,
        total_observations: totalObservations,
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

  // Filter history to exclude the current upload from the comparison dropdown
  const historyForComparison = (history || []).filter(
    (h) => h.upload_id !== uploadId
  );

  return (
    <div className="space-y-7">
      {/* KPI strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Total Observations" value={totalObservations?.toLocaleString()} color="blue" />
        <KPICard label="Safe Observations" value={safeCount?.toLocaleString()} color="green" />
        <KPICard label="At-Risk Observations" value={atRiskCount?.toLocaleString()} color="red" />
        <KPICard label="At-Risk Rate" value={`${atRiskPct}%`} color="orange" />
      </div>

      {/* Charts */}
      <ChartGrid chartData={chartData} />

      {/* AI summary with tabs */}
      <SummaryPanel
        userSummary={userSummary}
        managerSummary={managerSummary}
        dateRange={dateRange}
        onSendEmail={() => setShowEmailModal(true)}
        onDownload={handleDownload}
        downloading={downloading}
      />

      {/* Monthly comparison */}
      {historyForComparison.length > 0 && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
            <div>
              <h2 className="text-base font-semibold text-white">
                Compare with Previous Month
              </h2>
              <p className="text-xs text-gray-500 mt-0.5">
                Select a previous report to see trends and deltas
              </p>
            </div>
            <select
              value={compareUploadId}
              onChange={(e) => setCompareUploadId(e.target.value)}
              className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2.5
                         text-white text-sm focus:outline-none focus:border-blue-500
                         transition-colors min-w-[260px]"
            >
              <option value="">Select a previous upload...</option>
              {historyForComparison.map((h) => (
                <option key={h.upload_id} value={h.upload_id}>
                  {h.date_range} — {h.filename}
                </option>
              ))}
            </select>
          </div>

          {compareUploadId ? (
            <ComparisonView
              currentUploadId={uploadId}
              previousUploadId={compareUploadId}
            />
          ) : (
            <div className="border border-dashed border-gray-700 rounded-lg p-8 text-center">
              <p className="text-gray-500 text-sm">
                Choose a previous report above to compare metrics and trends
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
  };
  const valueColors = {
    blue: "text-blue-300",
    green: "text-green-300",
    red: "text-red-300",
    orange: "text-orange-300",
  };
  return (
    <div className={`rounded-xl border p-5 ${styles[color]}`}>
      <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">{label}</p>
      <p className={`text-3xl font-bold ${valueColors[color]}`}>{value}</p>
    </div>
  );
}
