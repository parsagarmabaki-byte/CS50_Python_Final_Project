import axios from "axios";
import { API_BASE } from "../config";

const client = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

client.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("fp_token");
  if (token) cfg.headers = { ...(cfg.headers || {}), Authorization: `Bearer ${token}` };
  return cfg;
});

export default client;
