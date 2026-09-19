from typing import List, Dict, Set

def check_circular_dependency(new_task_id: int, depends_on_task_id: int, current_dependencies: List[Dict[str, int]]) -> bool:
    """
    Returns True if adding (new_task_id -> depends_on_task_id) creates a cycle.
    current_dependencies is a list of dicts: {"task_id": x, "depends_on_task_id": y}
    """
    if new_task_id == depends_on_task_id:
        return True

    # Build graph: depends_on -> tasks that depend on it
    # We want to check if depends_on_task_id can reach new_task_id
    graph = {}
    for d in current_dependencies:
        dep = d["depends_on_task_id"]
        tid = d["task_id"]
        if dep not in graph:
            graph[dep] = []
        graph[dep].append(tid)

    # BFS or DFS to find if we can reach new_task_id starting from new_task_id going backwards through dependencies?
    # No, we're adding A -> B (A depends on B). So B must be done before A.
    # If B already (transitively) depends on A, we have a cycle.

    # Let's see if B depends on A
    # graph: task -> list of tasks it depends on
    adj = {}
    for d in current_dependencies:
        t = d["task_id"]
        dep = d["depends_on_task_id"]
        if t not in adj:
            adj[t] = []
        adj[t].append(dep)

    def dfs(current, target, visited):
        if current == target:
            return True
        visited.add(current)
        for nxt in adj.get(current, []):
            if nxt not in visited:
                if dfs(nxt, target, visited):
                    return True
        return False

    # If we add A -> B, we check if B can reach A (i.e. B depends on A)
    return dfs(depends_on_task_id, new_task_id, set())
