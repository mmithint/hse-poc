import SummaryTabs from "./SummaryTabs";

export default function SummaryPanel({
  userSummary,
  managerSummary,
  detailedSummary,
  categoryAnalysis,
  dateRange,
  onSendEmail,
  onDownload,
  downloading,
}) {
  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
      <div className="flex items-start justify-between gap-4 mb-5">
        <div>
          <h2 className="text-base font-semibold text-white">
            AI-Generated Summary
          </h2>
          {dateRange && (
            <p className="text-sm text-gray-400 mt-0.5">Period: {dateRange}</p>
          )}
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {/* Download PDF button */}
          <button
            onClick={onDownload}
            disabled={downloading}
            className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600
                       disabled:opacity-50 disabled:cursor-not-allowed
                       text-white px-4 py-2.5 rounded-lg text-sm font-medium
                       transition-colors duration-150"
          >
            {downloading ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10"
                    stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                Generating...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download PDF
              </>
            )}
          </button>

          {/* Send Email button */}
          <button
            onClick={onSendEmail}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500
                       active:bg-blue-700 text-white px-4 py-2.5 rounded-lg text-sm
                       font-medium transition-colors duration-150"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            Send Email Report
          </button>
        </div>
      </div>

      <SummaryTabs userSummary={userSummary} managerSummary={managerSummary} detailedSummary={detailedSummary} categoryAnalysis={categoryAnalysis} />
    </div>
  );
}
