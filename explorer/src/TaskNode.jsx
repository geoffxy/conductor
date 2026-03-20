import { useRef, useEffect, useState } from "react";
import { Handle, Position } from "@xyflow/react";
import { createPortal } from "react-dom";
import { VscInfo, VscSearch } from "react-icons/vsc";
import { format, formatDistanceToNow } from "date-fns";
import "./TaskNode.css";

function taskTypeClass(taskType) {
  if (taskType === "run_command") {
    return "command";
  } else if (taskType === "run_experiment") {
    return "experiment";
  } else if (taskType === "group") {
    return "group";
  } else if (taskType === "combine") {
    return "combine";
  } else {
    console.error("Unknown task type", taskType);
  }
}

function TaskInfoButton({
  buttonRef,
  showTooltip,
  onMouseEnter,
  onMouseLeave,
}) {
  return (
    <button
      ref={buttonRef}
      type="button"
      className="task-info-button"
      aria-label="Task info"
      aria-expanded={showTooltip}
      aria-haspopup="dialog"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <VscInfo />
    </button>
  );
}

function TaskVersionButton({ numVersions }) {
  return (
    <button
      type="button"
      className="task-version-button"
      aria-label={`View versions (${numVersions})`}
    >
      <VscSearch />
      <span className="task-version-count">{numVersions}</span>
    </button>
  );
}

function TaskInfoTooltip({ runnableDetails, anchorRef, showTooltip }) {
  const tooltipRef = useRef(null);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });

  useEffect(() => {
    if (!showTooltip) {
      return undefined;
    }

    const updateTooltipPosition = () => {
      if (!anchorRef.current) {
        return;
      }

      const rect = anchorRef.current.getBoundingClientRect();
      const tooltipHeight = tooltipRef.current?.offsetHeight ?? 160;
      const margin = 8;

      const top = Math.min(
        window.innerHeight - tooltipHeight - margin,
        Math.max(margin, rect.top + rect.height / 2 - tooltipHeight / 2),
      );
      const left = rect.right + 20;

      setTooltipPosition({ top, left });
    };

    updateTooltipPosition();
    window.addEventListener("resize", updateTooltipPosition);
    window.addEventListener("scroll", updateTooltipPosition, true);

    return () => {
      window.removeEventListener("resize", updateTooltipPosition);
      window.removeEventListener("scroll", updateTooltipPosition, true);
    };
  }, [anchorRef, showTooltip]);

  if (!showTooltip) {
    return null;
  }

  return createPortal(
    <div
      ref={tooltipRef}
      className="task-info-tooltip"
      role="dialog"
      aria-label="Task runnable details"
      style={{
        top: `${tooltipPosition.top}px`,
        left: `${tooltipPosition.left}px`,
      }}
      onClick={(event) => {
        event.stopPropagation();
      }}
      onMouseDown={(event) => {
        event.stopPropagation();
      }}
    >
      <TaskInfoTooltipContent runnableDetails={runnableDetails} />
    </div>,
    document.body,
  );
}

function TaskInfoTooltipContent({ runnableDetails }) {
  const runCommand = runnableDetails?.run ?? "";
  const args = Array.isArray(runnableDetails?.args) ? runnableDetails.args : [];
  const options =
    runnableDetails?.options && typeof runnableDetails.options === "object"
      ? Object.entries(runnableDetails.options)
      : [];

  return (
    <div className="tooltip-content">
      <div className="tooltip-section">
        <p>
          <strong>Run:</strong>
        </p>
        <pre>{runCommand}</pre>
      </div>

      {args.length > 0 && (
        <div className="tooltip-section">
          <p>
            <strong>Arguments:</strong>
          </p>
          <ul>
            {args.map((arg, index) => (
              <li key={`${arg}-${index}`}>
                <pre>{String(arg)}</pre>
              </li>
            ))}
          </ul>
        </div>
      )}
      {options.length > 0 && (
        <div className="tooltip-section">
          <p>
            <strong>Options:</strong>
          </p>
          <ul>
            {options.map(([key, value]) => (
              <li key={key}>
                <pre>
                  --{key} {String(value)}
                </pre>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function VersionBadge({ commitHash, timestamp }) {
  const shortHash = commitHash.slice(0, 7);
  const timestampDate = new Date(timestamp * 1000);
  const oneWeekInMs = 7 * 24 * 60 * 60 * 1000;
  const isOlderThanOneWeek = Date.now() - timestampDate.getTime() > oneWeekInMs;

  const formattedTime = isOlderThanOneWeek
    ? format(timestampDate, "yyyy-MM-dd 'at' HH:mm")
    : formatDistanceToNow(timestampDate, { addSuffix: true });

  return (
    <div className="version-badge">
      <div className="version-badge-hash">{shortHash}</div>
      <div className="version-badge-time">{formattedTime}</div>
    </div>
  );
}

function TaskVersionInfo({ versionInfo }) {
  const { versions, currentVersion } = versionInfo;
  const numVersions = versions?.length ?? 0;
  if (numVersions === 0) {
    return (
      <div className="task-version-info">
        <div>No versions available.</div>
      </div>
    );
  } else if (currentVersion == null) {
    // This means there are versions, but none are "relevant" based on the
    // current git commit.
    return (
      <div className="task-version-info">
        <div>No relevant version available.</div>
        <TaskVersionButton numVersions={numVersions} />
      </div>
    );
  } else {
    return (
      <div className="task-version-info">
        <VersionBadge
          commitHash={currentVersion.commit_hash}
          timestamp={currentVersion.timestamp}
        />
        <TaskVersionButton numVersions={numVersions} />
      </div>
    );
  }
}

const TaskNode = ({ data }) => {
  const nodeRef = useRef();
  const infoButtonRef = useRef(null);
  const [showTooltip, setShowTooltip] = useState(false);
  const { task, receiveNodeDimensions, versionInfo } = data;
  const taskTypeClassName = taskTypeClass(task.taskType);
  const hasRunnableDetails = task.runnableDetails != null;
  const shouldHaveVersions = task.taskType === "run_experiment";

  useEffect(() => {
    if (!hasRunnableDetails && showTooltip) {
      setShowTooltip(false);
    }
  }, [hasRunnableDetails, showTooltip]);

  useEffect(() => {
    if (nodeRef.current) {
      const { offsetWidth, offsetHeight } = nodeRef.current;
      const dims = { width: offsetWidth, height: offsetHeight };
      receiveNodeDimensions({ taskId: task.taskId, dimensions: dims });
    }
  }, [task, receiveNodeDimensions]);

  return (
    <>
      <Handle
        type="source"
        position={Position.Top}
        style={{ visibility: "hidden" }}
      />
      <div className={`task-node ${taskTypeClassName}`} ref={nodeRef}>
        <div className={`task-node-body-content ${taskTypeClassName}`}>
          <div className="task-top">
            <p className="task-id">{task.taskId.toString()}</p>
            {hasRunnableDetails ? (
              <div className="task-info-container">
                <TaskInfoButton
                  buttonRef={infoButtonRef}
                  showTooltip={showTooltip}
                  onMouseEnter={() => {
                    setShowTooltip(true);
                  }}
                  onMouseLeave={() => {
                    setShowTooltip(false);
                  }}
                />
                <TaskInfoTooltip
                  runnableDetails={task.runnableDetails}
                  anchorRef={infoButtonRef}
                  showTooltip={showTooltip}
                  onClose={() => {
                    setShowTooltip(false);
                  }}
                />
              </div>
            ) : null}
          </div>
          <div className="task-bottom">
            <p className="task-type">{task.taskType}</p>
          </div>
        </div>
        {shouldHaveVersions && <TaskVersionInfo versionInfo={versionInfo} />}
      </div>
      <Handle
        type="target"
        position={Position.Bottom}
        style={{ visibility: "hidden" }}
      />
    </>
  );
};

export default TaskNode;
