from string import hexdigits
from typing import Dict, List, Optional, Set, Tuple

from conductor.execution.version_index import Version
import conductor.explorer.models as m
from conductor.task_identifier import TaskIdentifier
from conductor.utils.git import Git


def _normalize_commit_token(token: str) -> Optional[str]:
    normalized = token.strip()
    if len(normalized) == 0:
        return None
    elif normalized[0] not in hexdigits:
        return normalized[1:]
    else:
        return normalized


def _parse_raw_graph_edges(
    raw_lines: List[str],
) -> Tuple[Set[str], List[Tuple[str, str]], Dict[str, str]]:
    edges = []
    commits = set()
    commit_messages = {}

    for line in raw_lines:
        stripped = line.strip()
        if len(stripped) == 0 or stripped.startswith("commit "):
            continue

        parts = stripped.split()
        if len(parts) < 1:
            continue

        child = _normalize_commit_token(parts[0])
        if child is None:
            continue
        commits.add(child)

        for parent_raw in parts[1:]:
            if parent_raw.startswith("|"):
                break

            parent = _normalize_commit_token(parent_raw)
            if parent is None:
                continue
            edges.append((child, parent))
            commits.add(parent)

        # Find commit message, which is everything after the first "|" character.
        if "|" in stripped:
            commit_message = stripped[stripped.index("|") + 1 :].strip()
        else:
            commit_message = ""
        commit_messages[child] = commit_message

    return commits, edges, commit_messages


def _to_version_node(
    commit_hash: str, versions: List[Version], commit_short_message: Optional[str]
) -> m.VersionGraphNode:
    result_versions = [m.ResultVersion.from_version(version) for version in versions]
    return m.VersionGraphNode(
        commit_hash=commit_hash,
        commit_short_message=commit_short_message,
        versions=sorted(
            result_versions,
            # Sort in descending order so that the most recent version for this commit is first.
            key=lambda v: -v.timestamp,
        ),
    )


def compute_version_graph(
    task_id: TaskIdentifier, versions: List[Version], git: Git
) -> m.VersionGraph:
    current_commit = git.current_commit()
    commit_to_versions: Dict[str, List[Version]] = {}
    for version in versions:
        if version.commit_hash is None:
            continue
        if version.commit_hash not in commit_to_versions:
            commit_to_versions[version.commit_hash] = []
        commit_to_versions[version.commit_hash].append(version)

    if len(commit_to_versions) == 0:
        return m.VersionGraph(
            task_id=m.TaskIdentifier.from_cond(task_id),
            current_commit=current_commit.hash if current_commit else None,
            selected_version=None,
            nodes=[],
            edges=[],
        )

    referenced_commits: Set[str] = set(commit_to_versions.keys())
    referenced_commits_list = list(referenced_commits)

    if current_commit is not None:
        referenced_commits.add(current_commit.hash)
        # Want to include HEAD to help with the visualization.
        referenced_commits_list.append(current_commit.hash)

    common_ancestor = git.get_common_ancestor(referenced_commits_list)

    # Special case: All disconnected commits.
    if common_ancestor is None:
        nodes = []
        for commit_hash in referenced_commits:
            versions = commit_to_versions.get(commit_hash, [])
            nodes.append(_to_version_node(commit_hash, versions, None))
        return m.VersionGraph(
            task_id=m.TaskIdentifier.from_cond(task_id),
            current_commit=current_commit.hash if current_commit else None,
            selected_version=None,
            nodes=nodes,
            edges=[],
        )

    referenced_commits.add(common_ancestor)
    referenced_commits_list.append(common_ancestor)
    raw_graph_out = git.get_raw_version_graph(
        commit_hashes=referenced_commits_list,
        terminate_hash=common_ancestor,
    )
    raw_commits, raw_edges, commit_messages = _parse_raw_graph_edges(raw_graph_out)

    # Construct adjacency lists to prepare for condensing
    adjacency: Dict[str, Set[str]] = {}
    reverse_adjacency: Dict[str, Set[str]] = {}
    all_commits: Set[str] = raw_commits | referenced_commits
    for child, parent in raw_edges:
        if child not in adjacency:
            adjacency[child] = set()
        if parent not in reverse_adjacency:
            reverse_adjacency[parent] = set()
        adjacency[child].add(parent)
        reverse_adjacency[parent].add(child)

    # Condense the graph by skipping over non-referenced linear paths, while
    # keeping track of skipped commits.
    commits_to_keep = set()
    for commit in all_commits:
        if commit in referenced_commits:
            commits_to_keep.add(commit)
            continue

        out_nodes = adjacency.get(commit, set())
        in_nodes = reverse_adjacency.get(commit, set())

        is_middle = len(out_nodes) == 1 and len(in_nodes) == 1
        is_end = len(out_nodes) == 0 and len(in_nodes) == 1
        is_start = len(out_nodes) == 1 and len(in_nodes) == 0
        should_remove = is_middle or is_end or is_start

        if not should_remove:
            commits_to_keep.add(commit)
            continue

        if is_middle:
            parent = next(iter(out_nodes))
            child = next(iter(in_nodes))
            adjacency[child].remove(commit)
            adjacency[child].add(parent)
            reverse_adjacency[parent].remove(commit)
            reverse_adjacency[parent].add(child)
        elif is_end:
            parent = next(iter(in_nodes))
            adjacency[parent].remove(commit)
            del reverse_adjacency[commit]
        elif is_start:
            child = next(iter(out_nodes))
            del adjacency[commit]
            reverse_adjacency[child].remove(commit)

    finalized_nodes = []
    finalized_edges = []
    for node in commits_to_keep:
        versions = commit_to_versions.get(node, [])
        commit_short_message = commit_messages.get(node)
        finalized_nodes.append(_to_version_node(node, versions, commit_short_message))
        next_commits = adjacency.get(node, set())
        for next_commit in next_commits:
            finalized_edges.append(
                m.VersionGraphEdge(
                    from_commit_hash=node,
                    to_commit_hash=next_commit,
                )
            )

    return m.VersionGraph(
        task_id=m.TaskIdentifier.from_cond(task_id),
        current_commit=current_commit.hash if current_commit else None,
        selected_version=None,
        nodes=finalized_nodes,
        edges=finalized_edges,
    )
