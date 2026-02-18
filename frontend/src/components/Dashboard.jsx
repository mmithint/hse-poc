import { useState } from "react";
import ChartGrid from "./ChartGrid";
import SummaryPanel from "./SummaryPanel";
import EmailModal from "./EmailModal";
import { downloadReport } from "../api/client";

export default function Dashboard({
  chartData,
  summary,
  dateRange,
  totalObservations,
  uploadId,
}) {
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const blob = await downloadReport({
        upload_id: uploadId,
        summary,
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

      {/* AI summary + email + download */}
      <SummaryPanel
        summary={summary}
        dateRange={dateRange}
        onSendEmail={() => setShowEmailModal(true)}
        onDownload={handleDownload}
        downloading={downloading}
      />

      {showEmailModal && (
        <EmailModal
          summary={summary}
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
    blue:   "bg-blue-950/50 border-blue-800/60",
    green:  "bg-green-950/50 border-green-800/60",
    red:    "bg-red-950/50 border-red-800/60",
    orange: "bg-orange-950/50 border-orange-800/60",
  };
  const valueColors = {
    blue:   "text-blue-300",
    green:  "text-green-300",
    red:    "text-red-300",
    orange: "text-orange-300",
  };
  return (
    <div className={`rounded-xl border p-5 ${styles[color]}`}>
      <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">{label}</p>
      <p className={`text-3xl font-bold ${valueColors[color]}`}>{value}</p>
    </div>
  );
}
