import { useCallback, useState } from "react";

export default function FileUpload({ onUpload }) {
  const [dragOver, setDragOver] = useState(false);

  const handleFile = useCallback(
    (file) => {
      if (!file) return;
      if (!file.name.match(/\.(xlsx|xls)$/i)) {
        alert("Please upload an Excel file (.xlsx or .xls)");
        return;
      }
      onUpload(file);
    },
    [onUpload]
  );

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragOver(false);
      handleFile(e.dataTransfer.files[0]);
    },
    [handleFile]
  );

  return (
    <div className="flex items-center justify-center min-h-[65vh]">
      <div className="w-full max-w-xl space-y-6 text-center">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">
            HSE Observation Analyzer
          </h2>
          <p className="text-gray-400 text-sm">
            Upload your Excel observation report to generate charts, an AI
            summary, and a VP-ready email.
          </p>
        </div>

        <div
          onDrop={handleDrop}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onClick={() => document.getElementById("excel-file-input").click()}
          className={[
            "border-2 border-dashed rounded-2xl p-14 cursor-pointer transition-all duration-200",
            dragOver
              ? "border-blue-400 bg-blue-950/40 scale-[1.01]"
              : "border-gray-600 hover:border-blue-500 bg-gray-900/40",
          ].join(" ")}
        >
          <div className="flex flex-col items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-blue-900/50 flex items-center justify-center">
              <svg
                className="w-8 h-8 text-blue-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            </div>
            <div>
              <p className="text-base font-medium text-gray-200">
                Drop your Excel file here
              </p>
              <p className="text-sm text-gray-500 mt-1">
                or{" "}
                <span className="text-blue-400 hover:text-blue-300">
                  click to browse
                </span>
              </p>
            </div>
            <p className="text-xs text-gray-600 bg-gray-800/60 px-3 py-1 rounded-full">
              .xlsx and .xls supported
            </p>
          </div>
          <input
            id="excel-file-input"
            type="file"
            accept=".xlsx,.xls"
            onChange={(e) => handleFile(e.target.files[0])}
            className="hidden"
          />
        </div>

        <p className="text-xs text-gray-600">
          Your file is processed locally and never stored permanently.
        </p>
      </div>
    </div>
  );
}
