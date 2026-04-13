import axios from "axios";

// React dev proxy (package.json "proxy") forwards all non-HTML requests to localhost:8000
const api = axios.create({ baseURL: "" });

export const predict         = (data)          => api.post("/predict", data);
export const saveActual      = (data)          => api.post("/actuals", data);
export const getMetrics      = ()              => api.get("/metrics");
export const getComparison   = ()              => api.get("/comparison");
export const getFeatureImp   = ()              => api.get("/feature-importance");
export const createStudent   = (data)          => api.post("/students", data);
export const listStudents    = ()              => api.get("/students");
export const listPredictions = ()              => api.get("/predictions");
export const listCSVStudents = ()              => api.get("/csv-students");
export const getCSVStudent   = (sid)           => api.get(`/csv-students/${sid}`);
