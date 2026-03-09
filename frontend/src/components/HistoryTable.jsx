import { useState } from "react";

export default function HistoryTable({ history, currentUploadId, onDelete }) {
  const [expandedId, setExpandedId] = useState(null);

  if (!history || history.length === 0) return null;

  const toggle = (id) => setExpandedId((prev) => (prev === id ? null : id));

  return (
    <div className="mt-10">
      <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-3">
        Previously Uploaded Reports
      </h2>
      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[640px]">
            <thead>
              <tr className="border-b border-gray-800 text-left bg-gray-800/30">
                <th className="px-4 py-3 text-xs text-gray-500 font-medium w-10">#</th>
                <th className="px-4 py-3 text-xs text-gray-500 font-medium">Filename</th>
                <th className="px-4 py-3 text-xs text-gray-500 font-medium">Uploaded By</th>
                <th className="px-4 py-3 text-xs text-gray-500 font-medium">Upload Date</th>
                <th className="px-4 py-3 text-xs text-gray-500 font-medium">Period</th>
                <th className="px-4 py-3 text-xs text-gray-500 font-medium text-right">Obs.</th>
                <th className="px-4 py-3 text-xs text-gray-500 font-medium text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item, idx) => (
                <HistoryRow
                  key={item.upload_id}
                  item={item}
                  index={idx + 1}
                  isCurrent={item.upload_id === currentUploadId}
                  isExpanded={expandedId === item.upload_id}
                  onToggle={() => toggle(item.upload_id)}
                  onDelete={onDelete}
                />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function HistoryRow({ item, index, isCurrent, isExpanded, onToggle, onDelete }) {
  const formattedDate = item.upload_date
    ? new Date(item.upload_date).toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
    : "—";

  return (
    <>
      <tr
        className={[
          "border-b border-gray-800/50 transition-colors",
          isCurrent ? "bg-blue-950/20" : "hover:bg-gray-800/30",
        ].join(" ")}
      >
        <td className="px-4 py-3 text-gray-500 text-xs">{index}</td>
        <td className="px-4 py-3">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span className="text-gray-200 font-medium truncate max-w-[200px]" title={item.filename}>
              {item.filename}
            </span>
            {isCurrent && (
              <span className="text-xs bg-blue-900/60 text-blue-300 px-1.5 py-0.5 rounded font-medium">
                Current
              </span>
            )}
          </div>
        </td>
        <td className="px-4 py-3 text-gray-400">{item.uploaded_by}</td>
        <td className="px-4 py-3 text-gray-400 text-xs">{formattedDate}</td>
        <td className="px-4 py-3 text-gray-400">{item.date_range}</td>
        <td className="px-4 py-3 text-gray-400 text-right font-mono">
          {item.total_observations.toLocaleString()}
        </td>
        <td className="px-4 py-3 text-center">
          <div className="inline-flex items-center gap-1.5">
            <button
              onClick={onToggle}
              className={[
                "inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg border transition-all",
                isExpanded
                  ? "text-gray-300 border-gray-600 bg-gray-700/50"
                  : "text-blue-400 border-blue-800/50 hover:border-blue-500 hover:bg-blue-900/20",
              ].join(" ")}
            >
              {isExpanded ? (
                <>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                  </svg>
                  Hide
                </>
              ) : (
                <>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                  View
                </>
              )}
            </button>
            <button
              onClick={() => {
                if (window.confirm("Delete this report?")) {
                  onDelete(item.upload_id);
                }
              }}
              disabled={isCurrent}
              title={isCurrent ? "Cannot delete the current upload" : "Delete this report"}
              className={[
                "inline-flex items-center justify-center w-7 h-7 rounded-lg border transition-all",
                isCurrent
                  ? "text-gray-600 border-gray-700 cursor-not-allowed opacity-40"
                  : "text-red-400 border-red-800/50 hover:border-red-500 hover:bg-red-900/20",
              ].join(" ")}
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </td>
      </tr>

      {isExpanded && (
        <tr className="bg-gray-800/20 border-b border-gray-800/50">
          <td colSpan={7} className="px-6 py-5">
            <HistoryDetail item={item} />
          </td>
        </tr>
      )}
    </>
  );
}

function HistoryDetail({ item }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(item.manager_summary || "");
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API not available
    }
  };

  if (!item.manager_summary && !item.user_summary) {
    return (
      <p className="text-gray-500 italic text-sm">
        No summary saved for this upload.
      </p>
    );
  }

  return (
    <div className="space-y-4 max-w-4xl">
      {item.manager_summary && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs text-gray-400 uppercase tracking-wide font-semibold">
              Manager Report
            </p>
            <button
              onClick={handleCopy}
              className={[
                "text-xs flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-colors",
                copied
                  ? "text-green-400 border-green-700 bg-green-900/20"
                  : "text-blue-400 border-blue-800/50 hover:border-blue-500 hover:bg-blue-900/20",
              ].join(" ")}
            >
              {copied ? (
                <>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Copied!
                </>
              ) : (
                <>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copy to Clipboard
                </>
              )}
            </button>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
              {item.manager_summary}
            </p>
          </div>
        </div>
      )}

      {item.user_summary && (
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-wide font-semibold mb-2">
            Detailed Summary
          </p>
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
              {item.user_summary}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
