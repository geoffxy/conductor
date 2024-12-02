import axios from "axios";

const API = "/api/1";

async function getTaskGraph() {
  const results = await axios.get(`${API}/task_graph`);
  return results.data;
}

export { getTaskGraph };
