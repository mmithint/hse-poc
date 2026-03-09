import axios from "axios";

// Using Vite proxy: baseURL is empty so requests go through the proxy at /api
const api = axios.create({
  baseURL: "",
  timeout: 90000, // 90s to accommodate Azure OpenAI latency
});

export const uploadFile = async (file, uploadedBy = "Unknown") => {
  const formData = new FormData();
  formData.append("uploaded_by", uploadedBy); // text field first
  formData.append("file", file);
  const res = await api.post("/api/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
};

export const generateSummary = async (payload) => {
  const res = await api.post("/api/summarize", payload);
  return res.data; // { user_summary, manager_summary }
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

export const getHistory = async () => {
  const res = await api.get("/api/history");
  return res.data; // { uploads: [...] }
};

export const getUploadDetail = async (uploadId) => {
  const res = await api.get(`/api/uploads/${uploadId}`);
  return res.data;
};

export const compareUploads = async (currentId, previousId) => {
  const res = await api.post("/api/compare", {
    current_upload_id: currentId,
    previous_upload_id: previousId,
  });
  return res.data;
};

export const multiCompare = async (uploadIds) => {
  const res = await api.post("/api/multi-compare", {
    upload_ids: uploadIds,
  });
  return res.data;
};

export const deleteUpload = async (uploadId) => {
  const res = await api.delete(`/api/uploads/${uploadId}`);
  return res.data;
};

export const downloadComparison = async (uploadIds) => {
  const res = await api.post("/api/download-comparison", {
    upload_ids: uploadIds,
  }, {
    responseType: "blob",
  });
  return res.data;
};
