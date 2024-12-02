import { getTaskGraph, getAllVersions } from "./api";
import Header from "./Header";
import MainDisplay from "./MainDisplay";
import { useEffect, useState } from "react";
import TaskIdentifier from "./models/identifier";

function parseRawTaskId({ path, name }) {
  return new TaskIdentifier(path, name);
}

const App = () => {
  const [taskGraph, setTaskGraph] = useState(null);
  const [versions, setVersions] = useState({});

  useEffect(() => {
    const fetchData = async () => {
      const taskGraphFuture = getTaskGraph();
      const versionsFuture = getAllVersions();
      const [taskGraph, versions] = await Promise.all([
        taskGraphFuture,
        versionsFuture,
      ]);

      // Task graph: light parsing.
      const rootTaskIds = [];
      for (const rawTaskId of taskGraph.root_tasks) {
        rootTaskIds.push(parseRawTaskId(rawTaskId));
      }
      const tasks = [];
      for (const rawTask of taskGraph.tasks) {
        const taskId = parseRawTaskId(rawTask.identifier);
        const deps = rawTask.deps.map(parseRawTaskId);
        tasks.push({
          taskId,
          deps,
          taskType: rawTask.task_type,
        });
      }
      setTaskGraph({
        rootTaskIds,
        tasks,
      });

      // Versions: light parsing.
      const parsedVersions = {};
      for (const rawVersion of versions) {
        const taskId = parseRawTaskId(rawVersion.identifier);
        parsedVersions[taskId.toString()] = {
          taskId,
          versions: rawVersion.versions,
        };
      }
      setVersions(parsedVersions);
    };
    fetchData();
  }, []);

  return (
    <div id="conductor-explorer">
      <Header />
      <MainDisplay taskGraph={taskGraph} versions={versions} />
    </div>
  );
};

export default App;
