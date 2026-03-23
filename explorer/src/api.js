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

async function getCommitInfo(commitHash) {
  const results = await axios.get(
    `${API}/commit_info?commit_hash=${commitHash}`,
  );
  return results.data;
}

async function setVersionOverride(taskId, timestamp) {
  const results = await axios.post(`${API}/version_override`, {
    task_id: taskId.toString(),
    timestamp,
  });
  return results.data;
}

async function clearVersionOverride(taskId) {
  const results = await axios.delete(`${API}/version_override`, {
    params: { task_id: taskId.toString() },
  });
  return results.data;
}

export {
  getTaskGraph,
  getAllVersions,
  getVersionsForTask,
  getCommitInfo,
  setVersionOverride,
  clearVersionOverride,
};
