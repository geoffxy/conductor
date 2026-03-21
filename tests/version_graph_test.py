import pathlib
from typing import List

from conductor.execution.version_index import Version
from conductor.explorer.version_graph import compute_version_graph
from conductor.task_identifier import TaskIdentifier


class _FakeGit:
    def __init__(self, common_ancestor: str, raw_graph_lines: List[str]):
        self._common_ancestor = common_ancestor
        self._raw_graph_lines = raw_graph_lines

    def get_common_ancestor(self, commit_hashes: List[str]) -> str:
        assert len(commit_hashes) > 0
        return self._common_ancestor

    def get_raw_version_graph(
        self, commit_hashes: List[str], terminate_hash: str
    ) -> List[str]:
        assert len(commit_hashes) > 0
        assert terminate_hash == self._common_ancestor
        return self._raw_graph_lines


def test_empty_when_all_versions_have_no_commit():
    versions = [
        Version(timestamp=100, commit_hash=None, has_uncommitted_changes=False),
        Version(timestamp=200, commit_hash=None, has_uncommitted_changes=True),
    ]

    task_id = TaskIdentifier(path=pathlib.Path("testing"), name="task")
    graph = compute_version_graph(
        task_id=task_id, versions=versions, git=_FakeGit("unused", [])
    )

    assert graph.nodes == []
    assert graph.edges == []


def test_condenses_linear_path():
    versions = [
        Version(timestamp=100, commit_hash="aaa", has_uncommitted_changes=False),
        Version(timestamp=200, commit_hash="ccc", has_uncommitted_changes=False),
    ]
    raw_graph_lines = [
        "commit aaa bbb",
        ">aaa bbb",
        "commit bbb ccc",
        ">bbb ccc",
        "commit -ccc ddd",
        "-ccc ddd",
    ]

    task_id = TaskIdentifier(path=pathlib.Path("testing"), name="task")
    graph = compute_version_graph(
        task_id=task_id,
        versions=versions,
        git=_FakeGit(common_ancestor="ddd", raw_graph_lines=raw_graph_lines),
    )
    actual_nodes = [node.commit_hash for node in graph.nodes]
    actual_nodes.sort()

    assert actual_nodes == ["aaa", "ccc", "ddd"]
    assert len(graph.edges) == 2
    edge_tuples = {(edge.from_commit_hash, edge.to_commit_hash) for edge in graph.edges}
    assert ("aaa", "ccc") in edge_tuples
    assert ("ccc", "ddd") in edge_tuples


def test_keeps_non_referenced_fork_or_join_nodes():
    versions = [
        Version(timestamp=100, commit_hash="a", has_uncommitted_changes=False),
        Version(timestamp=200, commit_hash="d", has_uncommitted_changes=False),
        Version(timestamp=300, commit_hash="e", has_uncommitted_changes=False),
    ]
    raw_graph_lines = [
        "commit a c",
        ">a c",
        "commit c d f",
        ">c d f",
        "commit f e",
        ">f e",
    ]

    task_id = TaskIdentifier(path=pathlib.Path("testing"), name="task")
    graph = compute_version_graph(
        task_id=task_id,
        versions=versions,
        git=_FakeGit(common_ancestor="z", raw_graph_lines=raw_graph_lines),
    )

    nodes_by_hash = {node.commit_hash: node for node in graph.nodes}
    assert "c" in nodes_by_hash
    assert "a" in nodes_by_hash
    assert "d" in nodes_by_hash
    assert "e" in nodes_by_hash

    edge_tuples = {(edge.from_commit_hash, edge.to_commit_hash) for edge in graph.edges}
    assert ("a", "c") in edge_tuples
    assert ("c", "e") in edge_tuples
    assert ("c", "d") in edge_tuples
    assert len(edge_tuples) == 3
