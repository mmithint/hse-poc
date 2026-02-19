import { useState } from "react";
import { sendEmailReport } from "../api/client";

export default function EmailModal({ managerSummary, uploadId, dateRange, onClose }) {
  const [email, setEmail] = useState("");
  const [subject, setSubject] = useState(
    `HSE Observation Report \u2013 ${dateRange}`
  );
  const [status, setStatus] = useState("idle"); // "idle" | "sending" | "sent" | "error"
  const [errorMsg, setErrorMsg] = useState("");

  const handleSend = async () => {
    if (!email || !email.includes("@")) {
      setErrorMsg("Please enter a valid email address.");
      return;
    }
    setStatus("sending");
    setErrorMsg("");
    try {
      await sendEmailReport({
        to_email: email,
        subject,
        manager_summary: managerSummary,
        upload_id: uploadId,
      });
      setStatus("sent");
    } catch (err) {
      setStatus("error");
      setErrorMsg(
        err.response?.data?.detail ?? "Failed to send. Check server configuration."
      );
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center
                 justify-center z-50 px-4"
      onClick={onClose}
    >
      <div
        className="bg-gray-900 rounded-2xl border border-gray-700 p-8 w-full
                   max-w-md shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {status === "sent" ? (
          <div className="text-center py-4">
            <div className="w-16 h-16 bg-green-900/50 rounded-full flex items-center
                           justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-green-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">
              Email Sent!
            </h3>
            <p className="text-gray-400 text-sm mb-6">
              Report successfully delivered to{" "}
              <span className="text-blue-400">{email}</span>
            </p>
            <button
              onClick={onClose}
              className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2
                         rounded-lg text-sm transition-colors"
            >
              Close
            </button>
          </div>
        ) : (
          <>
            <h3 className="text-xl font-semibold text-white mb-1">
              Send Email Report
            </h3>
            <p className="text-gray-400 text-sm mb-6">
              The AI summary and all 4 charts will be included in the email.
            </p>

            <div className="space-y-4">
              <FormField label="Recipient Email">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="vp@company.com"
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg
                             px-4 py-2.5 text-white placeholder-gray-500
                             focus:outline-none focus:border-blue-500 transition-colors text-sm"
                />
              </FormField>

              <FormField label="Subject">
                <input
                  type="text"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-600 rounded-lg
                             px-4 py-2.5 text-white focus:outline-none
                             focus:border-blue-500 transition-colors text-sm"
                />
              </FormField>

              {(status === "error" || errorMsg) && (
                <p className="text-red-400 text-sm bg-red-900/20 border border-red-800
                              rounded-lg px-4 py-2.5">
                  {errorMsg}
                </p>
              )}
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={onClose}
                className="flex-1 border border-gray-600 text-gray-300
                           hover:text-white hover:border-gray-400 py-2.5 rounded-lg
                           text-sm transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSend}
                disabled={status === "sending"}
                className="flex-1 bg-blue-600 hover:bg-blue-500 disabled:opacity-50
                           disabled:cursor-not-allowed text-white py-2.5 rounded-lg
                           text-sm font-medium transition-colors"
              >
                {status === "sending" ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg
                      className="w-4 h-4 animate-spin"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8v8z"
                      />
                    </svg>
                    Sending...
                  </span>
                ) : (
                  "Send Report"
                )}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function FormField({ label, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-300 mb-1.5">
        {label}
      </label>
      {children}
    </div>
  );
}
