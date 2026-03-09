import { useState } from "react";

export default function SummaryTabs({ userSummary, managerSummary, detailedSummary, categoryAnalysis }) {
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

  // Render markdown-style headers in detailed summary
  const renderDetailedSummary = (text) => {
    if (!text) return null;
    return text.split("\n").map((line, i) => {
      const trimmed = line.trim();
      if (trimmed.startsWith("## ")) {
        return (
          <h3 key={i} className="text-blue-300 font-semibold text-sm mt-4 mb-1">
            {trimmed.replace("## ", "")}
          </h3>
        );
      }
      if (trimmed.startsWith("# ")) {
        return (
          <h2 key={i} className="text-blue-200 font-bold text-base mt-4 mb-2">
            {trimmed.replace("# ", "")}
          </h2>
        );
      }
      if (!trimmed) return <br key={i} />;
      return (
        <p key={i} className="text-gray-200 text-sm leading-relaxed">
          {trimmed}
        </p>
      );
    });
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
        {detailedSummary && (
          <TabButton
            active={activeTab === "steven"}
            onClick={() => setActiveTab("steven")}
            label="Steven's Report"
          />
        )}
        {categoryAnalysis && categoryAnalysis.length > 0 && (
          <TabButton
            active={activeTab === "category"}
            onClick={() => setActiveTab("category")}
            label="Category Analysis"
          />
        )}
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

      {/* Steven's Report */}
      {activeTab === "steven" && (
        <div className="bg-gray-800/60 rounded-lg border border-gray-700 p-5">
          <div className="mb-3">
            <p className="text-xs text-gray-400 uppercase tracking-wide font-medium">
              HSE Director Report · Detailed Analysis
            </p>
          </div>
          {detailedSummary ? (
            <div>{renderDetailedSummary(detailedSummary)}</div>
          ) : (
            <p className="text-gray-500 italic text-sm">Detailed report not available.</p>
          )}
        </div>
      )}

      {/* Category Analysis */}
      {activeTab === "category" && (
        <div className="space-y-3">
          {categoryAnalysis && categoryAnalysis.length > 0 ? (
            categoryAnalysis.map((cat, idx) => (
              <div key={idx} className="bg-gray-800/60 rounded-lg border border-gray-700 p-5">
                <h4 className="text-sm font-semibold text-blue-300 mb-3">
                  {cat.category}
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Positive Trends */}
                  <div>
                    <p className="text-xs text-green-400 uppercase tracking-wide font-medium mb-2">
                      Positive Trends
                    </p>
                    <ul className="space-y-1.5">
                      {(cat.positive_trends || []).map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-200">
                          <span className="text-green-400 mt-0.5 flex-shrink-0">&#x2713;</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                  {/* Remaining Exposure */}
                  <div>
                    <p className="text-xs text-red-400 uppercase tracking-wide font-medium mb-2">
                      Remaining Exposure
                    </p>
                    <ul className="space-y-1.5">
                      {(cat.remaining_exposure || []).map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-gray-200">
                          <span className="text-red-400 mt-0.5 flex-shrink-0">&#x26A0;</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-500 italic text-sm">Category analysis not available.</p>
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
