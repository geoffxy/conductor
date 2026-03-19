import { useRef, useEffect } from "react";
import { Handle, Position } from "@xyflow/react";
import { VscInfo } from "react-icons/vsc";
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

function TaskInfoButton({ onClick }) {
  return (
    <button
      type="button"
      className="task-info-button"
      aria-label="Task info"
      title="Task info"
      onClick={onClick}
    >
      <VscInfo />
    </button>
  );
}

const TaskNode = ({ data }) => {
  const nodeRef = useRef();
  const { task, receiveNodeDimensions, versions } = data;
  const taskTypeClassName = taskTypeClass(task.taskType);

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
        <div className="task-top">
          <p className="task-id">{task.taskId.toString()}</p>
          {task.taskType == "run_experiment" ||
          task.taskType == "run_command" ? (
            <TaskInfoButton
              onClick={(event) => {
                event.stopPropagation();
              }}
            />
          ) : null}
        </div>
        <div className="task-bottom">
          <p className="task-type">{task.taskType}</p>
          {versions.length > 0 && (
            <p className="task-versions">Versions: {versions.length}</p>
          )}
        </div>
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
