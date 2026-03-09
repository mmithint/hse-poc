import { useState, useEffect } from "react";
import FileUpload from "./components/FileUpload";
import Dashboard from "./components/Dashboard";
import HistoryTable from "./components/HistoryTable";
import { uploadFile, generateSummary, getHistory, deleteUpload } from "./api/client";

const INITIAL = {
  phase: "idle",       // "idle" | "uploading" | "summarizing" | "dashboard"
  uploadId: null,
  chartData: null,
  dateRange: null,
  totalObservations: null,
  atRiskDescriptions: [],
  observationDetails: [],
  userSummary: null,
  managerSummary: null,
  detailedSummary: null,
  categoryAnalysis: [],
  error: null,
};

export default function App() {
  const [state, setState] = useState(INITIAL);
  const [history, setHistory] = useState([]);

  // Load upload history on mount
  useEffect(() => {
    getHistory()
      .then((data) => setHistory(data.uploads))
      .catch(() => {}); // fail silently — app works without history
  }, []);

  const patch = (updates) =>
    setState((prev) => ({ ...prev, ...updates }));

  const refreshHistory = () => {
    getHistory()
      .then((data) => setHistory(data.uploads))
      .catch(() => {});
  };

  const handleFileUpload = async (file, uploadedBy) => {
    patch({ phase: "uploading", error: null });

    try {
      const data = await uploadFile(file, uploadedBy);
      patch({
        phase: "summarizing",
        uploadId: data.upload_id,
        chartData: data.chart_data,
        dateRange: data.date_range,
        totalObservations: data.total_observations,
        atRiskDescriptions: data.atrisk_descriptions,
        observationDetails: data.observation_details || [],
      });

      const summaryData = await generateSummary({
        upload_id: data.upload_id,
        chart_data: data.chart_data,
        date_range: data.date_range,
        total_observations: data.total_observations,
        atrisk_descriptions: data.atrisk_descriptions,
        observation_details: data.observation_details || [],
      });

      // Merge intervention data from LLM response into chartData
      const mergedChartData = {
        ...data.chart_data,
        interventions_by_facility: summaryData.interventions_by_facility || {},
        total_interventions: summaryData.total_interventions || 0,
      };

      patch({
        phase: "dashboard",
        chartData: mergedChartData,
        userSummary: summaryData.user_summary,
        managerSummary: summaryData.manager_summary,
        detailedSummary: summaryData.detailed_summary || null,
        categoryAnalysis: summaryData.category_analysis || [],
      });

      // Refresh history so the new upload appears if user resets
      refreshHistory();
    } catch (err) {
      patch({
        phase: "idle",
        error:
          err.response?.data?.detail ??
          "Something went wrong. Please try again.",
      });
    }
  };

  const handleDeleteUpload = async (id) => {
    try {
      await deleteUpload(id);
      refreshHistory();
    } catch {
      // fail silently
    }
  };

  const handleReset = () => {
    refreshHistory();
    setState(INITIAL);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="bg-blue-950 border-b border-blue-900/60 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg
                className="w-5 h-5 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">
                HSE Observation Dashboard
              </h1>
              <p className="text-xs text-blue-300 leading-tight">
                Health, Safety &amp; Environment Reporting
              </p>
            </div>
          </div>

          {state.phase !== "idle" && (
            <button
              onClick={handleReset}
              className="text-sm text-blue-300 hover:text-white transition-colors
                         flex items-center gap-1.5"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
                />
              </svg>
              Upload New File
            </button>
          )}
        </div>
      </header>

      {/* Main */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Error banner */}
        {state.error && (
          <div
            className="mb-6 flex items-start gap-3 bg-red-900/30 border border-red-700/60
                          rounded-xl p-4 text-red-300 text-sm"
          >
            <svg
              className="w-5 h-5 flex-shrink-0 mt-0.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>{state.error}</span>
          </div>
        )}

        {state.phase === "idle" && (
          <>
            <FileUpload onUpload={handleFileUpload} />
            <HistoryTable history={history} currentUploadId={state.uploadId} onDelete={handleDeleteUpload} />
          </>
        )}

        {(state.phase === "uploading" || state.phase === "summarizing") && (
          <LoadingScreen phase={state.phase} />
        )}

        {state.phase === "dashboard" && (
          <Dashboard
            chartData={state.chartData}
            userSummary={state.userSummary}
            managerSummary={state.managerSummary}
            detailedSummary={state.detailedSummary}
            categoryAnalysis={state.categoryAnalysis}
            dateRange={state.dateRange}
            totalObservations={state.totalObservations}
            uploadId={state.uploadId}
            history={history}
          />
        )}
      </main>
    </div>
  );
}

function LoadingScreen({ phase }) {
  const messages = {
    uploading: "Parsing Excel data...",
    summarizing: "Generating AI summary...",
  };
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-5">
      <div className="relative">
        <div className="w-14 h-14 border-4 border-blue-900 rounded-full" />
        <div
          className="absolute inset-0 w-14 h-14 border-4 border-blue-500 border-t-transparent
                        rounded-full animate-spin"
        />
      </div>
      <div className="text-center">
        <p className="text-blue-300 text-sm font-medium">{messages[phase]}</p>
        <p className="text-gray-600 text-xs mt-1">
          {phase === "summarizing"
            ? "This may take 10-20 seconds"
            : "Just a moment..."}
        </p>
      </div>
    </div>
  );
}
