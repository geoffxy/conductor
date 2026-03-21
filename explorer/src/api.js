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

async function getVersionsForTask(taskId) {
  const encodedTaskId = encodeURIComponent(taskId.toString());
  const results = await axios.get(
    `${API}/version_graph?task_id=${encodedTaskId}`,
  );
  return results.data;
}

export { getTaskGraph, getAllVersions, getVersionsForTask };
