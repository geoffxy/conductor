import { useEffect, useRef } from "react";
import { Handle, Position } from "@xyflow/react";
import { VscLocation, VscSearch, VscCheck } from "react-icons/vsc";
import "./VersionNode.css";

function shortHash(commitHash) {
  return commitHash.slice(0, 7);
}

const VersionNode = ({ data }) => {
  const nodeRef = useRef();
  const {
    receiveNodeDimensions,
    commitHash,
    versions,
    isCurrentCommit,
    setFocusedCommitHash,
    isFocused,
    isSelected,
  } = data;
  const hasVersions = versions.length > 0;

  useEffect(() => {
    if (nodeRef.current) {
      const { offsetWidth, offsetHeight } = nodeRef.current;
      const dims = { width: offsetWidth, height: offsetHeight };
      receiveNodeDimensions({ commitHash, dimensions: dims });
    }
  }, [commitHash, receiveNodeDimensions]);

  const classNames = ["version-node"];

  // The styling has priority.
  if (isSelected) {
    classNames.push("selected");
  } else if (isFocused) {
    classNames.push("focused");
  } else if (hasVersions) {
    classNames.push("has-versions");
  }

  let icon = null;
  if (isSelected) {
    icon = <VscCheck />;
  } else if (isFocused) {
    icon = <VscSearch />;
  } else if (isCurrentCommit) {
    icon = <VscLocation />;
  }

  return (
    <>
      <Handle
        type="target"
        position={Position.Left}
        style={{ visibility: "hidden" }}
      />
      <div className={classNames.join(" ")} ref={nodeRef}>
        <div
          className="version-node-circle"
          onClick={() => {
            if (!hasVersions) return;
            if (isFocused) {
              setFocusedCommitHash(null);
            } else {
              setFocusedCommitHash(commitHash);
            }
          }}
        >
          {icon}
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
