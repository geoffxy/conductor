import { useMemo, useState, useCallback } from "react";
import {
  ReactFlow,
  ReactFlowProvider,
  Controls,
  MarkerType,
} from "@xyflow/react";
import TaskNode from "./TaskNode";
import Dagre from "@dagrejs/dagre";
import "@xyflow/react/dist/style.css";

function taskGraphToNodesAndEdges(taskGraph, receiveNodeDimensions) {
  const nodes = [];
  const edges = [];
  if (taskGraph == null) {
    return { nodes, edges };
  }

  for (const task of taskGraph.tasks) {
    nodes.push({
      id: task.taskId.toString(),
      data: { task, receiveNodeDimensions },
      type: "taskNode",
      // N.B. This is a placeholder position. We use Dagre to compute the actual
      // layout.
      position: { x: 0, y: 0 },
    });
    for (const dep of task.deps) {
      edges.push({
        id: `${dep.toString()}-${task.taskId.toString()}`,
        source: dep.toString(),
        target: task.taskId.toString(),
        markerEnd: { type: MarkerType.ArrowClosed },
      });
    }
  }
  return { nodes, edges };
}

function computeGraphLayout({ nodes, edges }, nodeDimensions) {
  const g = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "BT", ranksep: 40 });

  edges.forEach((edge) => g.setEdge(edge.source, edge.target));
  nodes.forEach((node) => {
    const dims = nodeDimensions[node.id] ?? { width: 0, height: 0 };
    g.setNode(node.id, {
      ...node,
      ...dims,
    });
  });

  Dagre.layout(g);

  return {
    nodes: nodes.map((node) => {
      const position = g.node(node.id);
      const dims = nodeDimensions[node.id] ?? { width: 0, height: 0 };
      // We are shifting the dagre node position (anchor=center center) to the top left
      // so it matches the React Flow node anchor point (top left).
      const x = position.x - dims.width / 2;
      const y = position.y - dims.height / 2;

      return { ...node, position: { x, y } };
    }),
    edges,
  };
}

const MainDisplayImpl = ({ taskGraph }) => {
  const nodeTypes = useMemo(() => ({ taskNode: TaskNode }), []);
  const [nodeDimensions, setNodeDimensions] = useState({});
  const receiveNodeDimensions = useCallback(
    ({ taskId, dimensions }) => {
      setNodeDimensions((prev) => ({
        ...prev,
        [taskId.toString()]: dimensions,
      }));
    },
    [setNodeDimensions],
  );
  const out = taskGraphToNodesAndEdges(taskGraph, receiveNodeDimensions);
  const { nodes, edges } = computeGraphLayout(out, nodeDimensions);

  return (
    <div
      style={{ height: "calc(100vh - 70px)", marginTop: "70px", zIndex: "1" }}
    >
      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView>
        <Controls />
      </ReactFlow>
    </div>
  );
};

const MainDisplay = ({ taskGraph }) => {
  return (
    <ReactFlowProvider>
      <MainDisplayImpl taskGraph={taskGraph} />
    </ReactFlowProvider>
  );
};

export default MainDisplay;
