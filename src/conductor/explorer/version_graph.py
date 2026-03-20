from string import hexdigits
from typing import Dict, List, Optional, Set, Tuple

from conductor.execution.version_index import Version
from conductor.explorer.models import VersionGraph, VersionGraphEdge, VersionGraphNode
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
) -> Tuple[Set[str], List[Tuple[str, str]]]:
    edges = []
    commits = set()

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
            parent = _normalize_commit_token(parent_raw)
            if parent is None:
                continue
            edges.append((child, parent))

    return commits, edges


def compute_version_graph(
    task_id: TaskIdentifier, versions: List[Version], git: Git
) -> VersionGraph:
    commit_to_versions: Dict[str, List[Version]] = {}
    for version in versions:
        if version.commit_hash is None:
            continue
        if version.commit_hash not in commit_to_versions:
            commit_to_versions[version.commit_hash] = []
        commit_to_versions[version.commit_hash].append(version)

    if len(commit_to_versions) == 0:
        return VersionGraph(nodes=[], edges=[])

    referenced_commits: Set[str] = set(commit_to_versions.keys())
    common_ancestor = git.get_common_ancestor(list(referenced_commits))

    # Special case: All disconnected commits.
    if common_ancestor is None:
        nodes = [
            VersionGraphNode(
                commit_hash=commit_hash,
                versions=sorted(
                    commit_to_versions[commit_hash],
                    key=lambda v: v.timestamp,
                ),
                is_referenced=True,
                is_fork_or_join=False,
            )
            for commit_hash in sorted(referenced_commits)
        ]
        return VersionGraph(nodes=nodes, edges=[])

    raw_graph_out = git.get_raw_version_graph(
        commit_hashes=list(referenced_commits),
        terminate_hash=common_ancestor,
    )
    raw_commits, raw_edges = _parse_raw_graph_edges(raw_graph_out)

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
    for commit in all_commits:
        if commit in referenced_commits:
            continue

        out_nodes = adjacency.get(commit, set())
        in_nodes = reverse_adjacency.get(commit, set())
        if not (len(out_nodes) == 1 and len(in_nodes) == 1):
            continue

        parent = next(iter(out_nodes))
        child = next(iter(in_nodes))
        adjacency[child].remove(commit)
        adjacency[child].add(parent)
        reverse_adjacency[parent].remove(commit)
        reverse_adjacency[parent].add(child)

    finalized_nodes = []
    finalized_edges = []

    for node in all_commits:
        finalized_nodes.append(
            VersionGraphNode(
                commit_hash=node,
                versions=sorted(
                    commit_to_versions.get(node, []),
                    # Sort in descending order so that the most recent version for
                    # this commit is first.
                    key=lambda v: -v.timestamp,
                ),
            )
        )
        next_commits = adjacency.get(node, set())
        for next_commit in next_commits:
            finalized_edges.append(
                VersionGraphEdge(
                    from_commit_hash=node,
                    to_commit_hash=next_commit,
                )
            )

    return VersionGraph(task_id=task_id, nodes=finalized_nodes, edges=finalized_edges)
