import { useRef, useEffect } from "react";
import { Handle, Position } from "@xyflow/react";
import "./TaskNode.css";

const TaskNode = ({ data }) => {
  const nodeRef = useRef();
  const { task, receiveNodeDimensions } = data;

  useEffect(() => {
    if (nodeRef.current) {
      const { offsetWidth, offsetHeight } = nodeRef.current;
      const dims = { width: offsetWidth, height: offsetHeight };
      receiveNodeDimensions({ taskId: task.taskId, dimensions: dims });
    }
  }, [task, receiveNodeDimensions]);

  return (
    <>
      <Handle type="source" position={Position.Top} />
      <div className="task-node" ref={nodeRef}>
        <p>{task.taskId.toString()}</p>
      </div>
      <Handle type="target" position={Position.Bottom} />
    </>
  );
};

export default TaskNode;
