import { useRef, useEffect } from "react";
import { Handle, Position } from "@xyflow/react";
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

const TaskNode = ({ data }) => {
  const nodeRef = useRef();
  const { task, receiveNodeDimensions } = data;
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
        <p className="task-id">{task.taskId.toString()}</p>
        <p className="task-type">{task.taskType}</p>
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
