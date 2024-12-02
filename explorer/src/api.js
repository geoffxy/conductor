import axios from "axios";

const API = "/api/1";

async function getTaskGraph() {
  const results = await axios.get(`${API}/task_graph`);
  return results.data;
}

async function getAllVersions() {
  const results = await axios.get(`${API}/results/all_versions`);
  return results.data;
}

export { getTaskGraph, getAllVersions };
