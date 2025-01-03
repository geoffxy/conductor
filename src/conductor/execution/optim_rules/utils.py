from conductor.execution.ops.operation import Operation


def unlink_op(op: Operation) -> None:
    """
    Removes this operation from its containing graph.
    """

    # Our dependencies
    exe_deps = op.exe_deps
    # Tasks that depend on us
    deps_of = op.deps_of

    for dep in exe_deps:
        dep.deps_of.remove(op)

    for dep_of in deps_of:
        dep_of.exe_deps.remove(op)

    # Tasks that depend on us now have our dependencies.
    for dep_of in deps_of:
        for dep in exe_deps:
            dep_of.add_exe_dep(dep)

    # Our dependencies are now forwarded to our deps_of
    for dep in exe_deps:
        for dep_of in deps_of:
            dep.add_dep_of(dep_of)
