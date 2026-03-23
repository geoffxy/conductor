import "./VersionGraphSidebar.css";
import { useEffect, useState } from "react";
import { format, formatDistanceToNow } from "date-fns";
import { VscGitCommit } from "react-icons/vsc";
import { getCommitInfo } from "./api";

function humanReadableTimestamp(date) {
  const oneWeekInMs = 7 * 24 * 60 * 60 * 1000;
  const isOlderThanOneWeek = Date.now() - date.getTime() > oneWeekInMs;

  const formattedTime = isOlderThanOneWeek
    ? format(date, "yyyy-MM-dd 'at' HH:mm")
    : formatDistanceToNow(date, { addSuffix: true });

  return formattedTime;
}

function NoInfoMessage() {
  return (
    <div className="version-graph-sidebar-no-info">
      No relevant or selected version for this task.
    </div>
  );
}

function CommitInfo({ commitInfo }) {
  const timestampDate = new Date(commitInfo.date);
  const formattedTime = humanReadableTimestamp(timestampDate);

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

function VersionSelector({ commitInfo, existingCheckedVersion, versionList }) {
  const [currCheckedVersion, setCurrCheckedVersion] = useState(null);

  // Handle external changes to the existing checked version.
  useEffect(() => {
    if (
      existingCheckedVersion != null &&
      commitInfo.commit_hash === existingCheckedVersion.commit_hash
    ) {
      // If the existing checked version corresponds to the currently displayed
      // commit, we want to have it pre-selected in the radio options.
      setCurrCheckedVersion(existingCheckedVersion);
    } else {
      setCurrCheckedVersion(null);
    }
  }, [setCurrCheckedVersion, existingCheckedVersion, commitInfo]);

  // Enable submit if there is a currently checked version that is different
  // from the existing checked version (if it exists).
  let enableSubmit = false;
  if (currCheckedVersion != null) {
    if (existingCheckedVersion != null) {
      if (commitInfo.commit_hash !== existingCheckedVersion.commit_hash) {
        // If the currently checked version corresponds to a different commit than
        // the existing checked version, we want to enable the submit button.
        enableSubmit = true;
      } else if (
        currCheckedVersion.timestamp !== existingCheckedVersion.timestamp
      ) {
        // If the currently checked version has a different timestamp than the
        // existing checked version (but corresponds to the same commit), we also
        // want to enable the submit button since it represents a different version.
        enableSubmit = true;
      }
    } else {
      // If there is no existing checked version, then any selected version should be
      // submittable.
      enableSubmit = true;
    }
  }

  return (
    <div className="version-selector">
      <div className="version-selector-heading">Experiment versions</div>
      <form className="version-selector-form">
        {versionList.map((version) => {
          const formattedTime = humanReadableTimestamp(
            new Date(version.timestamp * 1000),
          );
          return (
            <label key={version.timestamp} className="version-selector-option">
              <input
                type="radio"
                name="version"
                value={version.timestamp}
                checked={
                  currCheckedVersion &&
                  currCheckedVersion.timestamp === version.timestamp
                }
                onChange={() => setCurrCheckedVersion(version)}
              />
              <span className="version-selector-option-message">
                From {formattedTime}
              </span>
            </label>
          );
        })}
        <button type="submit" disabled={!enableSubmit}>
          Use this version
        </button>
        <button type="reset">Cancel</button>
      </form>
    </div>
  );
}

function SidebarBody({ commitInfo, existingCheckedVersion, versionList }) {
  return (
    <div className="version-graph-sidebar-body">
      <CommitInfo commitInfo={commitInfo} />
      <VersionSelector
        commitInfo={commitInfo}
        existingCheckedVersion={existingCheckedVersion}
        versionList={versionList}
      />
    </div>
  );
}

function VersionGraphSidebar({
  selectedVersion,
  versionList,
  focusedCommitHash,
}) {
  const [displayInfo, setDisplayInfo] = useState({
    commitInfo: null,
    existingCheckedVersion: null,
  });

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
        existingCheckedVersion:
          selectedVersion.commit_hash === commitHashToFetch
            ? selectedVersion
            : null,
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
          existingCheckedVersion={displayInfo.existingCheckedVersion}
          versionList={versionList}
        />
      )}
    </div>
  );
}

export default VersionGraphSidebar;
