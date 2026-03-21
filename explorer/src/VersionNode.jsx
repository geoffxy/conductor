import { useEffect, useRef } from "react";
import { Handle, Position } from "@xyflow/react";
import "./VersionNode.css";

function shortHash(commitHash) {
  return commitHash.slice(0, 7);
}

const VersionNode = ({ data }) => {
  const nodeRef = useRef();
  const { receiveNodeDimensions, commitHash, hasVersions } = data;

  useEffect(() => {
    if (nodeRef.current) {
      const { offsetWidth, offsetHeight } = nodeRef.current;
      const dims = { width: offsetWidth, height: offsetHeight };
      receiveNodeDimensions({ commitHash, dimensions: dims });
    }
  }, [commitHash, receiveNodeDimensions]);

  const classNames = ["version-node"];
  if (!hasVersions) {
    classNames.push("no-versions");
  }

  return (
    <>
      <Handle
        type="target"
        position={Position.Left}
        style={{ visibility: "hidden" }}
      />
      <div className={classNames.join(" ")} title={commitHash} ref={nodeRef}>
        <span className="version-node-label">{shortHash(commitHash)}</span>
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
