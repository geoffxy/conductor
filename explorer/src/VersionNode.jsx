import { useEffect, useRef } from "react";
import { Handle, Position } from "@xyflow/react";
import { VscLocation } from "react-icons/vsc";
import "./VersionNode.css";

function shortHash(commitHash) {
  return commitHash.slice(0, 7);
}

const VersionNode = ({ data }) => {
  const nodeRef = useRef();
  const { receiveNodeDimensions, commitHash, versions, isCurrentCommit } = data;
  const hasVersions = versions.length > 0;

  useEffect(() => {
    if (nodeRef.current) {
      const { offsetWidth, offsetHeight } = nodeRef.current;
      const dims = { width: offsetWidth, height: offsetHeight };
      receiveNodeDimensions({ commitHash, dimensions: dims });
    }
  }, [commitHash, receiveNodeDimensions]);

  return (
    <>
      <Handle
        type="target"
        position={Position.Left}
        style={{ visibility: "hidden" }}
      />
      <div
        className={`version-node ${isCurrentCommit ? "current" : ""} ${hasVersions ? "has-versions" : ""}`}
        ref={nodeRef}
      >
        <div className="version-node-circle">
          {isCurrentCommit && <VscLocation />}
        </div>
        <div className="version-node-label">
          <span>{shortHash(commitHash)}</span>
          {isCurrentCommit && <span>(HEAD)</span>}
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Right}
        style={{ visibility: "hidden" }}
      />
    </>
  );
};

export default VersionNode;
