import { useMemo, useState, useCallback, useEffect } from "react";
import {
  ReactFlow,
  ReactFlowProvider,
  Controls,
  MarkerType,
} from "@xyflow/react";
import Dagre from "@dagrejs/dagre";
import { VscClose } from "react-icons/vsc";
import VersionNode from "./VersionNode";
import VersionGraphSidebar from "./VersionGraphSidebar";
import "@xyflow/react/dist/style.css";
import "./VersionGraphDisplay.css";

function versionGraphToNodesAndEdges(
  versionGraph,
  receiveNodeDimensions,
  { currentCommit, selectedVersion, focusedCommitHash, setFocusedCommitHash },
) {
  const nodes = [];
  const edges = [];

  if (versionGraph == null) {
    return { nodes, edges };
  }

  for (const versionNode of versionGraph.nodes ?? []) {
    const commitHash = versionNode.commit_hash;
    const commitShortMessage = versionNode.commit_short_message;
    const versions = Array.isArray(versionNode.versions)
      ? versionNode.versions
      : [];

    // Current commit: Git repository HEAD.
    // Focused commit: The version node that is currently focused/selected in
    //                 the UI. This may be null (no version node is focused).
    // Selected commit: The commit corresponding to the version that is
    //                  currently selected in Conductor (either the relevant version or
    //                  overridden commit).
    // Note that these are not mutually exclusive - all three can be the same commit.
    nodes.push({
      id: commitHash,
      data: {
        receiveNodeDimensions,
        commitHash,
        versions,
        commitShortMessage,
        isCurrentCommit: commitHash === currentCommit,
        isFocused: commitHash === focusedCommitHash,
        isSelected: commitHash === selectedVersion?.commit_hash,
        someNodeFocused: focusedCommitHash != null,
        setFocusedCommitHash,
      },
      type: "versionNode",
      // N.B. This is a placeholder position. We use Dagre to compute the actual
      // layout.
      position: { x: 0, y: 0 },
      draggable: false,
    });
  }

  for (const edge of versionGraph.edges ?? []) {
    // Git commit edges go from commit to parent commit (new -> old).
    // We want to display the direction in the opposite way (old -> new) since
    // it feels more natural to read left to right, so we flip the source and
    // target here.
    edges.push({
      id: `${edge.from_commit_hash}-${edge.to_commit_hash}`,
      source: edge.to_commit_hash,
      target: edge.from_commit_hash,
      markerEnd: { type: MarkerType.ArrowClosed },
      type: "smoothstep",
    });
  }

  return { nodes, edges };
}

function computeGraphLayout({ nodes, edges }, nodeDimensions) {
  const g = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "LR", ranksep: 48, nodesep: 32 });

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

const VersionGraphDisplayImpl = ({
  taskId,
  currentCommit,
  selectedVersion,
  versionGraph,
  clearViewVersions,
  refreshVersions,
}) => {
  const nodeTypes = useMemo(() => ({ versionNode: VersionNode }), []);
  const [nodeDimensions, setNodeDimensions] = useState({});
  // Represents the commit hash of the version node that is currently
  // focused/selected in the graph.
  const [focusedCommitHash, setFocusedCommitHash] = useState(null);

  const receiveNodeDimensions = useCallback(
    ({ commitHash, dimensions }) => {
      setNodeDimensions((prev) => ({
        ...prev,
        [commitHash]: dimensions,
      }));
    },
    [setNodeDimensions],
  );

  const out = versionGraphToNodesAndEdges(versionGraph, receiveNodeDimensions, {
    currentCommit,
    selectedVersion,
    focusedCommitHash,
    setFocusedCommitHash,
  });
  const { nodes, edges } = computeGraphLayout(out, nodeDimensions);

  useEffect(() => {
    const handleKeyUp = (event) => {
      if (event.key === "Escape") {
        clearViewVersions();
      }
    };

    window.addEventListener("keyup", handleKeyUp);
    return () => {
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [clearViewVersions]);

  const versionList = [];
  for (const node of versionGraph?.nodes ?? []) {
    if (focusedCommitHash != null) {
      if (node.commit_hash === focusedCommitHash) {
        versionList.push(...node.versions);
      }
    } else if (selectedVersion != null) {
      if (node.commit_hash === selectedVersion.commit_hash) {
        versionList.push(...node.versions);
      }
    }
  }

  return (
    <div className="version-graph-overlay" onClick={() => clearViewVersions()}>
      <div
        className="version-graph-display"
        style={{ height: "80%", width: "80%" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="version-graph-header">
          <div className="version-graph-task-id">{taskId.toString()}</div>
          <button
            type="button"
            className="version-graph-close-button"
            aria-label="Close version graph"
            onClick={clearViewVersions}
          >
            <VscClose />
          </button>
        </div>
        <div className="version-graph-body">
          <div className="version-graph-flow-wrap">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              fitView
              zIndex="0"
            >
              <Controls />
            </ReactFlow>
          </div>
          <div className="version-graph-sidebar-wrap">
            <VersionGraphSidebar
              taskId={taskId}
              selectedVersion={selectedVersion}
              versionList={versionList}
              focusedCommitHash={focusedCommitHash}
              closeModal={clearViewVersions}
              refreshVersions={refreshVersions}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

const VersionGraphDisplay = (props) => {
  return (
    <ReactFlowProvider>
      <VersionGraphDisplayImpl {...props} />
    </ReactFlowProvider>
  );
};

export default VersionGraphDisplay;
