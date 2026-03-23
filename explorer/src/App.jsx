import { getTaskGraph, getAllVersions, getVersionsForTask } from "./api";
import Header from "./Header";
import MainDisplay from "./MainDisplay";
import VersionGraphDisplay from "./VersionGraphDisplay";
import { useCallback, useEffect, useState } from "react";
import TaskIdentifier from "./models/identifier";

function parseRawTaskId({ path, name }) {
  return new TaskIdentifier(path, name);
}

async function fetchAndParseVersions() {
  const versions = await getAllVersions();
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
  return parsedVersions;
}

const App = () => {
  const [taskGraph, setTaskGraph] = useState(null);
  const [versions, setVersions] = useState({});
  const [viewVersions, setViewVersions] = useState(null);

  const clearViewVersions = useCallback(() => {
    setViewVersions(null);
  }, [setViewVersions]);
  const showVersionsForTask = useCallback(
    async (taskId) => {
      const versions = await getVersionsForTask(taskId);
      const parsed = {
        taskId,
        // This represents the current location in the Git repository (i.e., the
        // HEAD commit).
        currentCommit: versions.current_commit,
        // The version of this task being used (it's either the most relevant
        // version, or the overridden version if the user has selected one).
        selectedVersion: versions.selected_version,
        // The full version graph for display.
        versionGraph: {
          nodes: versions.nodes,
          edges: versions.edges,
        },
      };
      setViewVersions(parsed);
    },
    [setViewVersions],
  );

  useEffect(() => {
    const fetchData = async () => {
      const taskGraphFuture = getTaskGraph();
      const versionsFuture = fetchAndParseVersions();
      const [taskGraph, parsedVersions] = await Promise.all([
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

      setVersions(parsedVersions);
    };
    fetchData();
  }, []);

  const refreshVersions = useCallback(async () => {
    const parsedVersions = await fetchAndParseVersions();
    setVersions(parsedVersions);
  }, [setVersions]);

  return (
    <div id="conductor-explorer">
      <Header />
      <MainDisplay
        taskGraph={taskGraph}
        versions={versions}
        showVersionsForTask={showVersionsForTask}
      />
      {viewVersions != null && (
        <VersionGraphDisplay
          {...viewVersions}
          clearViewVersions={clearViewVersions}
          refreshVersions={refreshVersions}
        />
      )}
    </div>
  );
};

export default App;
