import { ReactFlow, Controls, MarkerType } from "@xyflow/react";
import Dagre from "@dagrejs/dagre";
import "@xyflow/react/dist/style.css";

function taskGraphToNodesAndEdges(taskGraph) {
  const nodes = [];
  const edges = [];
  if (taskGraph == null) {
    return { nodes, edges };
  }

  for (const { taskId, deps } of taskGraph.tasks) {
    nodes.push({
      id: taskId.toString(),
      data: { label: taskId.toString() },
    });
    for (const dep of deps) {
      edges.push({
        id: `${dep.toString()}-${taskId.toString()}`,
        source: dep.toString(),
        target: taskId.toString(),
        markerEnd: { type: MarkerType.ArrowClosed },
      });
    }
  }
  return { nodes, edges };
}

function computeGraphLayout({ nodes, edges }) {
  const g = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "TB", ranksep: 80, });

  edges.forEach((edge) => g.setEdge(edge.source, edge.target));
  nodes.forEach((node) =>
    g.setNode(node.id, {
      ...node,
      width: node.measured?.width ?? 0,
      height: node.measured?.height ?? 0,
    }),
  );

  Dagre.layout(g);

  return {
    nodes: nodes.map((node) => {
      const position = g.node(node.id);
      // We are shifting the dagre node position (anchor=center center) to the top left
      // so it matches the React Flow node anchor point (top left).
      const x = position.x - (node.measured?.width ?? 0) / 2;
      const y = position.y - (node.measured?.height ?? 0) / 2;

      return { ...node, position: { x, y } };
    }),
    edges,
  };
}

const MainDisplay = ({ taskGraph }) => {
  const nodeEdges = taskGraphToNodesAndEdges(taskGraph);
  const { nodes, edges } = computeGraphLayout(nodeEdges);

  return (
    <div
      style={{ height: "calc(100vh - 70px)", marginTop: "70px", zIndex: "1" }}
    >
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Controls />
      </ReactFlow>
    </div>
  );
};

export default MainDisplay;
