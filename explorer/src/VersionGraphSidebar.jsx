import "./VersionGraphSidebar.css";
import { useEffect, useState, useCallback } from "react";
import { format, formatDistanceToNow } from "date-fns";
import { VscGitCommit } from "react-icons/vsc";
import { getCommitInfo } from "./api";

function NoInfoMessage() {
  return (
    <div className="version-graph-sidebar-no-info">
      No relevant or selected version for this task.
    </div>
  );
}

function CommitInfo({ commitInfo }) {
  const timestampDate = new Date(commitInfo.date);
  const oneWeekInMs = 7 * 24 * 60 * 60 * 1000;
  const isOlderThanOneWeek = Date.now() - timestampDate.getTime() > oneWeekInMs;

  const formattedTime = isOlderThanOneWeek
    ? format(timestampDate, "yyyy-MM-dd 'at' HH:mm")
    : formatDistanceToNow(timestampDate, { addSuffix: true });

  const headingMessage = commitInfo.message[0];
  const detailedMessage = commitInfo.message.slice(1).join("\n").trim();

  return (
    <div className="version-graph-sidebar-commit-info">
      <div className="version-graph-sidebar-commit-info-message">
        {headingMessage}
      </div>
      <div className="version-graph-sidebar-commit-info-details">
        <div className="commit-hash">
          <span>
            <VscGitCommit />
          </span>
          <span>{commitInfo.commit_hash.slice(0, 7)}</span>
        </div>
        <div className="timestamp">Committed {formattedTime}</div>
        <div className="added">+{commitInfo.lines_added}</div>
        <div className="removed">-{commitInfo.lines_removed}</div>
      </div>
      {detailedMessage && (
        <div className="version-graph-sidebar-commit-info-detailed">
          {detailedMessage}
        </div>
      )}
    </div>
  );
}

function VersionSelector() {
  return <div />;
}

function SidebarBody({ commitInfo, checkedVersion, setCheckedVersion }) {
  return (
    <div className="version-graph-sidebar-body">
      <CommitInfo commitInfo={commitInfo} />
      <VersionSelector
        checkedVersion={checkedVersion}
        setCheckedVersion={setCheckedVersion}
      />
    </div>
  );
}

function VersionGraphSidebar({ selectedVersion, focusedCommitHash }) {
  const [displayInfo, setDisplayInfo] = useState({
    commitInfo: null,
    checkedVersion: null,
  });
  const setCheckedVersion = useCallback(
    (version) => {
      setDisplayInfo((prev) => ({
        ...prev,
        checkedVersion: version,
      }));
    },
    [setDisplayInfo],
  );

  useEffect(() => {
    const fetchCommitInfo = async () => {
      let commitHashToFetch = null;
      if (focusedCommitHash != null) {
        commitHashToFetch = focusedCommitHash;
      } else if (selectedVersion != null) {
        commitHashToFetch = selectedVersion.commit_hash;
      }

      if (commitHashToFetch == null) return;

      const commitInfo = await getCommitInfo(commitHashToFetch);
      setDisplayInfo({
        commitInfo,
        checkedVersion: selectedVersion,
      });
    };
    fetchCommitInfo();
  }, [selectedVersion, focusedCommitHash]);

  const showNoInfo = displayInfo.commitInfo == null;

  return (
    <div className="version-graph-sidebar">
      {showNoInfo ? (
        <NoInfoMessage />
      ) : (
        <SidebarBody
          commitInfo={displayInfo.commitInfo}
          checkedVersion={displayInfo.checkedVersion}
          setCheckedVersion={setCheckedVersion}
        />
      )}
    </div>
  );
}

export default VersionGraphSidebar;
