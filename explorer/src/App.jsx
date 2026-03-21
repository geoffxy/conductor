import { getTaskGraph, getAllVersions } from "./api";
import Header from "./Header";
import MainDisplay from "./MainDisplay";
import VersionGraphDisplay from "./VersionGraphDisplay";
import { useEffect, useState } from "react";
import TaskIdentifier from "./models/identifier";

function parseRawTaskId({ path, name }) {
  return new TaskIdentifier(path, name);
}

const App = () => {
  const [taskGraph, setTaskGraph] = useState(null);
  const [versions, setVersions] = useState({});
  const [viewTaskVersions, setViewTaskVersions] = useState(null);

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
          runnableDetails: rawTask.runnable_details,
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
          currentVersion: rawVersion.current_version,
        };
      }
      setVersions(parsedVersions);
    };
    fetchData();
  }, []);

  return (
    <div id="conductor-explorer">
      <Header />
      <MainDisplay
        taskGraph={taskGraph}
        versions={versions}
        setViewTaskVersions={setViewTaskVersions}
      />
      {viewTaskVersions != null && (
        <VersionGraphDisplay {...viewTaskVersions} />
      )}
    </div>
  );
};

export default App;
