import { useState } from "react";

export default function SummaryTabs({ userSummary, managerSummary }) {
  const [activeTab, setActiveTab] = useState("user");
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(managerSummary || "");
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API not available
    }
  };

  return (
    <div>
      {/* Tab bar */}
      <div className="flex gap-1 mb-4 bg-gray-800/50 rounded-lg p-1 w-fit">
        <TabButton
          active={activeTab === "user"}
          onClick={() => setActiveTab("user")}
          label="Detailed View"
        />
        <TabButton
          active={activeTab === "manager"}
          onClick={() => setActiveTab("manager")}
          label="Manager Report"
        />
      </div>

      {/* Detailed View */}
      {activeTab === "user" && (
        <div className="bg-gray-800/60 rounded-lg border border-gray-700 p-5">
          {userSummary ? (
            <p className="text-gray-200 text-sm leading-relaxed whitespace-pre-wrap">
              {userSummary}
            </p>
          ) : (
            <p className="text-gray-500 italic text-sm">Summary not available.</p>
          )}
        </div>
      )}

      {/* Manager Report */}
      {activeTab === "manager" && (
        <div className="bg-gray-800/60 rounded-lg border border-gray-700 p-5">
          <div className="flex justify-between items-center mb-3">
            <p className="text-xs text-gray-400 uppercase tracking-wide font-medium">
              Email-ready · 3-5 key points
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
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Copied!
                </>
              ) : (
                <>
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copy to Clipboard
                </>
              )}
            </button>
          </div>
          {managerSummary ? (
            <p className="text-gray-200 text-sm leading-relaxed whitespace-pre-wrap">
              {managerSummary}
            </p>
          ) : (
            <p className="text-gray-500 italic text-sm">Manager summary not available.</p>
          )}
        </div>
      )}
    </div>
  );
}

function TabButton({ active, onClick, label }) {
  return (
    <button
      onClick={onClick}
      className={[
        "px-4 py-2 rounded-md text-sm font-medium transition-colors",
        active
          ? "bg-blue-600 text-white shadow-sm"
          : "text-gray-400 hover:text-white",
      ].join(" ")}
    >
      {label}
    </button>
  );
}
