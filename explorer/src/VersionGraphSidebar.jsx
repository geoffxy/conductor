import "./VersionGraphSidebar.css";

function NoInfoMessage() {
  return <span>No relevant or selected version for this task.</span>;
}

function VersionGraphSidebar() {
  return (
    <div className="version-graph-sidebar">
      <NoInfoMessage />
    </div>
  );
}

export default VersionGraphSidebar;
