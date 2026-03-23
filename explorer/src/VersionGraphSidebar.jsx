import "./VersionGraphSidebar.css";
import { useEffect, useState, useCallback } from "react";
import { format, formatDistanceToNow } from "date-fns";
import { VscGitCommit } from "react-icons/vsc";
import Button from "@mui/joy/Button";
import Radio from "@mui/joy/Radio";
import RadioGroup from "@mui/joy/RadioGroup";
import { getCommitInfo, setVersionOverride } from "./api";

function humanReadableTimestamp(date) {
  const oneWeekInMs = 7 * 24 * 60 * 60 * 1000;
  const isOlderThanOneWeek = Date.now() - date.getTime() > oneWeekInMs;

  const fullTime = format(date, "yyyy-MM-dd 'at' HH:mm");
  const formattedTime = isOlderThanOneWeek
    ? fullTime
    : formatDistanceToNow(date, { addSuffix: true });

  return { formattedTime, fullTime };
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
  const { formattedTime, fullTime } = humanReadableTimestamp(timestampDate);

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
        <div className="timestamp" title={`Committed ${fullTime}`}>
          Committed {formattedTime}
        </div>
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

function VersionSelector({
  taskId,
  commitInfo,
  existingCheckedVersion,
  versionList,
  closeModal,
  refreshVersions,
}) {
  const [currCheckedVersion, setCurrCheckedVersion] = useState(null);
  const [updateInProgress, setUpdateInProgress] = useState(false);

  const onSetVersionOverride = useCallback(async () => {
    if (currCheckedVersion == null) return;
    setUpdateInProgress(true);
    try {
      await setVersionOverride(taskId, currCheckedVersion.timestamp);
      await refreshVersions();
      closeModal();
    } finally {
      setUpdateInProgress(false);
    }
  }, [
    currCheckedVersion,
    taskId,
    setUpdateInProgress,
    refreshVersions,
    closeModal,
  ]);

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
      <div className="version-selector-heading">
        {versionList.length > 1
          ? "Experiment result versions"
          : "Experiment result version"}
      </div>
      <form className="version-selector-form">
        <div className="version-selector-wrap">
          <RadioGroup name="version-selector">
            {versionList.map((version) => {
              const { formattedTime } = humanReadableTimestamp(
                new Date(version.timestamp * 1000),
              );
              return (
                <Radio
                  key={version.timestamp}
                  name="version"
                  value={version.timestamp}
                  checked={
                    currCheckedVersion &&
                    currCheckedVersion.timestamp === version.timestamp
                  }
                  onChange={() => setCurrCheckedVersion(version)}
                  label={`From ${formattedTime}`}
                />
              );
            })}
          </RadioGroup>
        </div>
        <div className="version-selector-buttons">
          <Button
            color="primary"
            variant="soft"
            disabled={!enableSubmit}
            loading={updateInProgress}
            onClick={onSetVersionOverride}
          >
            Use this version
          </Button>
          <Button color="neutral" variant="soft" onClick={closeModal}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}

function SidebarBody({
  taskId,
  commitInfo,
  existingCheckedVersion,
  versionList,
  closeModal,
  refreshVersions,
}) {
  return (
    <div className="version-graph-sidebar-body">
      <CommitInfo commitInfo={commitInfo} />
      <VersionSelector
        taskId={taskId}
        commitInfo={commitInfo}
        existingCheckedVersion={existingCheckedVersion}
        versionList={versionList}
        closeModal={closeModal}
        refreshVersions={refreshVersions}
      />
    </div>
  );
}

function VersionGraphSidebar({
  taskId,
  selectedVersion,
  versionList,
  focusedCommitHash,
  closeModal,
  refreshVersions,
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
          selectedVersion != null &&
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
          taskId={taskId}
          commitInfo={displayInfo.commitInfo}
          existingCheckedVersion={displayInfo.existingCheckedVersion}
          versionList={versionList}
          closeModal={closeModal}
          refreshVersions={refreshVersions}
        />
      )}
    </div>
  );
}

export default VersionGraphSidebar;
