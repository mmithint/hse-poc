import axios from "axios";

// Using Vite proxy: baseURL is empty so requests go through the proxy at /api
const api = axios.create({
  baseURL: "",
  timeout: 90000, // 90s to accommodate Azure OpenAI latency
});

export const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post("/api/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
};

export const generateSummary = async (payload) => {
  const res = await api.post("/api/summarize", payload);
  return res.data;
};

export const sendEmailReport = async (payload) => {
  const res = await api.post("/api/send-email", payload);
  return res.data;
};

export const downloadReport = async (payload) => {
  const res = await api.post("/api/download-report", payload, {
    responseType: "blob",
  });
  return res.data; // Blob
};
