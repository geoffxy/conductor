import { ReactFlow, Controls } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

function taskGraphToNodesAndEdges(taskGraph) {
  const nodes = [];
  const edges = [];
  if (taskGraph == null) {
    return { nodes, edges };
  }

  let counter = 0;
  for (const { taskId, deps } of taskGraph.tasks) {
    nodes.push({
      id: taskId.toString(),
      position: { x: 0, y: counter * 100 },
      data: { label: taskId.toString() },
    });
    counter++;
    for (const dep of deps) {
      edges.push({
        id: `${dep.toString()}-${taskId.toString()}`,
        source: dep.toString(),
        target: taskId.toString(),
        markerEnd: { type: "arrowclosed" },
      });
    }
  }
  return { nodes, edges };
}

const MainDisplay = ({ taskGraph }) => {
  const { nodes, edges } = taskGraphToNodesAndEdges(taskGraph);

  return (
    <div
      style={{ height: "calc(100vh - 70px)", marginTop: "70px", zIndex: "1" }}
    >
      <ReactFlow nodes={nodes} edges={edges}>
        <Controls />
      </ReactFlow>
    </div>
  );
};

export default MainDisplay;
