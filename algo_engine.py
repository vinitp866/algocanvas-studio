import heapq
import math
from collections import deque


def _build_adj(graph: dict):
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_ids = [str(n["id"]) for n in nodes]
    pos = {str(n["id"]): (float(n.get("x", 0.0)), float(n.get("y", 0.0))) for n in nodes}

    adj = {nid: [] for nid in node_ids}
    clean_edges = []
    for e in edges:
        u = str(e.get("source", ""))
        v = str(e.get("target", ""))
        if u not in adj or v not in adj or u == v:
            continue
        try:
            w = float(e.get("weight", 1))
        except (ValueError, TypeError):
            w = 1.0
        clean_edges.append((u, v, w))
        adj[u].append((v, w))
        adj[v].append((u, w))

    for nid in adj:
        adj[nid].sort(key=lambda item: (item[1], item[0]))

    return node_ids, clean_edges, adj, pos


def _step(
    *,
    action: str,
    explanation: str,
    visited=None,
    frontier=None,
    frontier_label="Frontier",
    current_node=None,
    active_edge=None,
    distances=None,
    tree_edges=None,
    path_nodes=None,
    total_weight=None,
):
    return {
        "action": action,
        "explanation": explanation,
        "visited": list(visited or []),
        "frontier": [str(x) for x in (frontier or [])],
        "frontier_label": frontier_label,
        "current_node": str(current_node) if current_node is not None else None,
        "active_edge": list(active_edge) if active_edge else None,
        "distances": dict(distances or {}),
        "tree_edges": [list(te) for te in (tree_edges or [])],
        "path_nodes": [str(x) for x in (path_nodes or [])],
        "total_weight": total_weight,
    }


def _reconstruct_path(parent: dict, start_id: str, target_id: str):
    if target_id not in parent and target_id != start_id:
        return []
    path = []
    curr = target_id
    seen = set()
    while curr is not None and curr not in seen:
        seen.add(curr)
        path.append(curr)
        if curr == start_id:
            break
        curr = parent.get(curr)
    path.reverse()
    return path if path and path[0] == start_id else []


def _fmt_dist(val):
    if math.isinf(val):
        return "∞"
    return int(val) if float(val).is_integer() else round(val, 2)


def run_bfs(graph: dict, start_id: str):
    node_ids, _, adj, _ = _build_adj(graph)
    if start_id not in adj:
        return [_step(action="error", explanation=f"Start node '{start_id}' not found.")]

    visited = [start_id]
    seen = {start_id}
    queue = deque([start_id])
    tree_edges = []
    steps = [
        _step(
            action="init",
            explanation=f"BFS initialized at node {start_id} using a FIFO queue.",
            visited=visited,
            frontier=list(queue),
            frontier_label="Queue (FIFO)",
            current_node=start_id,
            tree_edges=tree_edges,
        )
    ]

    while queue:
        u = queue.popleft()
        steps.append(
            _step(
                action="pop",
                explanation=f"Dequeued {u} from front of queue to explore neighbors.",
                visited=visited,
                frontier=list(queue),
                frontier_label="Queue (FIFO)",
                current_node=u,
                tree_edges=tree_edges,
            )
        )
        for v, _ in adj[u]:
            steps.append(
                _step(
                    action="inspect_edge",
                    explanation=f"Inspecting edge {u} — {v}.",
                    visited=visited,
                    frontier=list(queue),
                    frontier_label="Queue (FIFO)",
                    current_node=u,
                    active_edge=(u, v),
                    tree_edges=tree_edges,
                )
            )
            if v not in seen:
                seen.add(v)
                visited.append(v)
                queue.append(v)
                tree_edges.append((u, v))
                steps.append(
                    _step(
                        action="visit",
                        explanation=f"Discovered unvisited node {v}; added to tree and enqueued.",
                        visited=visited,
                        frontier=list(queue),
                        frontier_label="Queue (FIFO)",
                        current_node=v,
                        active_edge=(u, v),
                        tree_edges=tree_edges,
                    )
                )

    steps.append(
        _step(
            action="complete",
            explanation=f"BFS complete. Visited {len(visited)} of {len(node_ids)} nodes in level order.",
            visited=visited,
            frontier=[],
            frontier_label="Queue (FIFO)",
            tree_edges=tree_edges,
            path_nodes=visited,
        )
    )
    return steps


def run_dfs(graph: dict, start_id: str):
    node_ids, _, adj, _ = _build_adj(graph)
    if start_id not in adj:
        return [_step(action="error", explanation=f"Start node '{start_id}' not found.")]

    visited = []
    seen = set()
    tree_edges = []
    parent = {}
    steps = [
        _step(
            action="init",
            explanation=f"DFS initialized at start node {start_id}.",
            visited=[],
            frontier=[start_id],
            frontier_label="Call Stack",
            current_node=start_id,
        )
    ]

    def dfs_visit(u, stack_view):
        seen.add(u)
        visited.append(u)
        steps.append(
            _step(
                action="visit",
                explanation=f"Entered node {u} and marked visited.",
                visited=visited,
                frontier=stack_view,
                frontier_label="Call Stack",
                current_node=u,
                active_edge=(parent[u], u) if u in parent else None,
                tree_edges=tree_edges,
            )
        )
        for v, _ in adj[u]:
            steps.append(
                _step(
                    action="inspect_edge",
                    explanation=f"Checking neighbor {v} from {u}.",
                    visited=visited,
                    frontier=stack_view + [v],
                    frontier_label="Call Stack",
                    current_node=u,
                    active_edge=(u, v),
                    tree_edges=tree_edges,
                )
            )
            if v not in seen:
                parent[v] = u
                tree_edges.append((u, v))
                dfs_visit(v, stack_view + [v])
                steps.append(
                    _step(
                        action="backtrack",
                        explanation=f"Backtracked to {u} after exploring {v}.",
                        visited=visited,
                        frontier=stack_view,
                        frontier_label="Call Stack",
                        current_node=u,
                        tree_edges=tree_edges,
                    )
                )

    dfs_visit(start_id, [start_id])
    steps.append(
        _step(
            action="complete",
            explanation=f"DFS complete. Visited {len(visited)} of {len(node_ids)} nodes.",
            visited=visited,
            frontier=[],
            frontier_label="Call Stack",
            tree_edges=tree_edges,
            path_nodes=visited,
        )
    )
    return steps


def run_dijkstra(graph: dict, start_id: str, target_id=None):
    node_ids, _, adj, _ = _build_adj(graph)
    if start_id not in adj:
        return [_step(action="error", explanation=f"Start node '{start_id}' not found.")]

    dist = {nid: math.inf for nid in node_ids}
    dist[start_id] = 0.0
    parent = {}
    settled = []
    settled_set = set()
    tree_edges = []
    pq = [(0.0, start_id)]

    steps = [
        _step(
            action="init",
            explanation=f"Dijkstra initialized: dist[{start_id}] = 0, all other nodes = ∞.",
            visited=settled,
            frontier=[f"{start_id}(0)"],
            frontier_label="Min-Heap (dist, node)",
            current_node=start_id,
            distances={k: _fmt_dist(v) for k, v in dist.items()},
        )
    ]

    while pq:
        d, u = heapq.heappop(pq)
        if u in settled_set:
            continue
        settled_set.add(u)
        settled.append(u)
        if u in parent:
            tree_edges.append((parent[u], u))

        steps.append(
            _step(
                action="settle",
                explanation=f"Settled node {u} with shortest distance {_fmt_dist(d)}.",
                visited=settled,
                frontier=[f"{n}({_fmt_dist(c)})" for c, n in sorted(pq)],
                frontier_label="Min-Heap (dist, node)",
                current_node=u,
                active_edge=(parent[u], u) if u in parent else None,
                distances={k: _fmt_dist(v) for k, v in dist.items()},
                tree_edges=tree_edges,
            )
        )

        if target_id and u == target_id:
            break

        for v, w in adj[u]:
            if v in settled_set:
                continue
            nd = d + w
            steps.append(
                _step(
                    action="relax_check",
                    explanation=f"Checking edge {u} — {v} (w={_fmt_dist(w)}): candidate {_fmt_dist(nd)} vs {_fmt_dist(dist[v])}.",
                    visited=settled,
                    frontier=[f"{n}({_fmt_dist(c)})" for c, n in sorted(pq)],
                    frontier_label="Min-Heap (dist, node)",
                    current_node=u,
                    active_edge=(u, v),
                    distances={k: _fmt_dist(v) for k, v in dist.items()},
                    tree_edges=tree_edges,
                )
            )
            if nd < dist[v]:
                dist[v] = nd
                parent[v] = u
                heapq.heappush(pq, (nd, v))
                steps.append(
                    _step(
                        action="relax",
                        explanation=f"Updated dist[{v}] = {_fmt_dist(nd)} via {u}.",
                        visited=settled,
                        frontier=[f"{n}({_fmt_dist(c)})" for c, n in sorted(pq)],
                        frontier_label="Min-Heap (dist, node)",
                        current_node=v,
                        active_edge=(u, v),
                        distances={k: _fmt_dist(v) for k, v in dist.items()},
                        tree_edges=tree_edges,
                    )
                )

    path_nodes = _reconstruct_path(parent, start_id, target_id) if target_id else settled
    cost = _fmt_dist(dist[target_id]) if (target_id and not math.isinf(dist.get(target_id, math.inf))) else None
    steps.append(
        _step(
            action="complete",
            explanation=(
                f"Shortest path to {target_id}: {' -> '.join(path_nodes)} (cost {_fmt_dist(dist[target_id])})."
                if (target_id and path_nodes)
                else f"Dijkstra finished settling {len(settled)} nodes."
            ),
            visited=settled,
            frontier=[],
            frontier_label="Min-Heap (dist, node)",
            distances={k: _fmt_dist(v) for k, v in dist.items()},
            tree_edges=tree_edges,
            path_nodes=path_nodes,
            total_weight=cost,
        )
    )
    return steps


def run_bellman_ford(graph: dict, start_id: str, target_id=None):
    node_ids, clean_edges, _, _ = _build_adj(graph)
    if start_id not in node_ids:
        return [_step(action="error", explanation=f"Start node '{start_id}' not found.")]

    directed_edges = []
    for u, v, w in clean_edges:
        directed_edges.append((u, v, w))
        directed_edges.append((v, u, w))

    dist = {nid: math.inf for nid in node_ids}
    dist[start_id] = 0.0
    parent = {}
    steps = [
        _step(
            action="init",
            explanation=f"Bellman-Ford initialized: dist[{start_id}] = 0 across {len(node_ids)} vertices.",
            visited=[start_id],
            frontier=[f"Pass 1/{max(1, len(node_ids) - 1)}"],
            frontier_label="Relaxation Pass",
            current_node=start_id,
            distances={k: _fmt_dist(v) for k, v in dist.items()},
        )
    ]

    num_passes = max(1, len(node_ids) - 1)
    for i in range(1, num_passes + 1):
        changed = False
        for u, v, w in directed_edges:
            if math.isinf(dist[u]):
                continue
            cand = dist[u] + w
            if cand < dist[v]:
                dist[v] = cand
                parent[v] = u
                changed = True
                steps.append(
                    _step(
                        action="relax",
                        explanation=f"Pass {i}: relaxed ({u} -> {v}, w={_fmt_dist(w)}), dist[{v}] = {_fmt_dist(cand)}.",
                        visited=[n for n in node_ids if not math.isinf(dist[n])],
                        frontier=[f"Pass {i}/{num_passes}"],
                        frontier_label="Relaxation Pass",
                        current_node=v,
                        active_edge=(u, v),
                        distances={k: _fmt_dist(v) for k, v in dist.items()},
                        tree_edges=[(parent[k], k) for k in parent],
                    )
                )
        if not changed:
            break

    tree_edges = [(parent[k], k) for k in parent]
    path_nodes = _reconstruct_path(parent, start_id, target_id) if target_id else [n for n in node_ids if not math.isinf(dist[n])]
    cost = _fmt_dist(dist[target_id]) if (target_id and not math.isinf(dist.get(target_id, math.inf))) else None
    steps.append(
        _step(
            action="complete",
            explanation=(
                f"Bellman-Ford path to {target_id}: {' -> '.join(path_nodes)} (cost {_fmt_dist(dist[target_id])})."
                if (target_id and path_nodes)
                else "Bellman-Ford edge relaxation complete."
            ),
            visited=[n for n in node_ids if not math.isinf(dist[n])],
            frontier=[],
            frontier_label="Relaxation Pass",
            distances={k: _fmt_dist(v) for k, v in dist.items()},
            tree_edges=tree_edges,
            path_nodes=path_nodes,
            total_weight=cost,
        )
    )
    return steps


def run_prims(graph: dict, start_id: str):
    node_ids, _, adj, _ = _build_adj(graph)
    if start_id not in adj:
        return [_step(action="error", explanation=f"Start node '{start_id}' not found.")]

    in_mst = [start_id]
    mst_set = {start_id}
    mst_edges = []
    total_w = 0.0
    pq = []
    for v, w in adj[start_id]:
        heapq.heappush(pq, (w, start_id, v))

    steps = [
        _step(
            action="init",
            explanation=f"Prim's MST started at root {start_id}.",
            visited=in_mst,
            frontier=[f"{u}-{v}({_fmt_dist(w)})" for w, u, v in sorted(pq)],
            frontier_label="Candidate Cut Edges",
            current_node=start_id,
            tree_edges=mst_edges,
            total_weight=0,
        )
    ]

    while pq and len(mst_set) < len(node_ids):
        w, u, v = heapq.heappop(pq)
        if v in mst_set:
            continue
        mst_set.add(v)
        in_mst.append(v)
        mst_edges.append((u, v))
        total_w += w

        steps.append(
            _step(
                action="add_mst_edge",
                explanation=f"Added minimum cut edge {u} — {v} (weight {_fmt_dist(w)}). Running MST weight = {_fmt_dist(total_w)}.",
                visited=in_mst,
                frontier=[f"{a}-{b}({_fmt_dist(c)})" for c, a, b in sorted(pq) if b not in mst_set],
                frontier_label="Candidate Cut Edges",
                current_node=v,
                active_edge=(u, v),
                tree_edges=mst_edges,
                total_weight=_fmt_dist(total_w),
            )
        )

        for nxt, nw in adj[v]:
            if nxt not in mst_set:
                heapq.heappush(pq, (nw, v, nxt))

    steps.append(
        _step(
            action="complete",
            explanation=f"Prim's MST complete with {len(mst_edges)} edges and total weight {_fmt_dist(total_w)}.",
            visited=in_mst,
            frontier=[],
            frontier_label="Candidate Cut Edges",
            tree_edges=mst_edges,
            path_nodes=in_mst,
            total_weight=_fmt_dist(total_w),
        )
    )
    return steps


def run_kruskal(graph: dict, start_id=None):
    node_ids, clean_edges, _, _ = _build_adj(graph)
    parent = {nid: nid for nid in node_ids}
    rank = {nid: 0 for nid in node_ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        if rank[ra] < rank[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        if rank[ra] == rank[rb]:
            rank[ra] += 1
        return True

    sorted_edges = sorted(clean_edges, key=lambda item: (item[2], item[0], item[1]))
    mst_edges = []
    mst_nodes = []
    mst_node_set = set()
    total_w = 0.0

    steps = [
        _step(
            action="init",
            explanation=f"Kruskal's MST sorted {len(sorted_edges)} edges by weight using Union-Find.",
            visited=[],
            frontier=[f"{u}-{v}({_fmt_dist(w)})" for u, v, w in sorted_edges],
            frontier_label="Sorted Edges",
            total_weight=0,
        )
    ]

    for idx, (u, v, w) in enumerate(sorted_edges):
        remaining = [f"{a}-{b}({_fmt_dist(c)})" for a, b, c in sorted_edges[idx + 1:]]
        if union(u, v):
            mst_edges.append((u, v))
            total_w += w
            for x in (u, v):
                if x not in mst_node_set:
                    mst_node_set.add(x)
                    mst_nodes.append(x)
            steps.append(
                _step(
                    action="add_mst_edge",
                    explanation=f"Edge {u} — {v} (w={_fmt_dist(w)}) connects distinct components; added to MST.",
                    visited=mst_nodes,
                    frontier=remaining,
                    frontier_label="Sorted Edges",
                    current_node=v,
                    active_edge=(u, v),
                    tree_edges=mst_edges,
                    total_weight=_fmt_dist(total_w),
                )
            )
        else:
            steps.append(
                _step(
                    action="skip_cycle",
                    explanation=f"Skipped edge {u} — {v} (w={_fmt_dist(w)}) because {u} and {v} share a component (cycle).",
                    visited=mst_nodes,
                    frontier=remaining,
                    frontier_label="Sorted Edges",
                    current_node=u,
                    active_edge=(u, v),
                    tree_edges=mst_edges,
                    total_weight=_fmt_dist(total_w),
                )
            )

    steps.append(
        _step(
            action="complete",
            explanation=f"Kruskal's MST complete: {len(mst_edges)} edges, total weight {_fmt_dist(total_w)}.",
            visited=mst_nodes,
            frontier=[],
            frontier_label="Sorted Edges",
            tree_edges=mst_edges,
            path_nodes=mst_nodes,
            total_weight=_fmt_dist(total_w),
        )
    )
    return steps


def run_astar(graph: dict, start_id: str, target_id=None, heuristics=None):
    node_ids, _, adj, pos = _build_adj(graph)
    if start_id not in adj:
        return [_step(action="error", explanation=f"Start node '{start_id}' not found.")]

    goal = target_id if (target_id and target_id in adj) else (node_ids[-1] if node_ids else start_id)
    custom_h = heuristics or {}

    max_span = 1.0
    if pos:
        xs = [p[0] for p in pos.values()]
        ys = [p[1] for p in pos.values()]
        max_span = max(1.0, math.hypot(max(xs) - min(xs), max(ys) - min(ys)))
    avg_w = 1.0
    all_w = [w for _, nbrs in adj.items() for _, w in nbrs]
    if all_w:
        avg_w = max(0.5, sum(all_w) / len(all_w))

    def h(nid):
        if str(nid) in custom_h:
            try:
                return float(custom_h[str(nid)])
            except (ValueError, TypeError):
                pass
        if nid not in pos or goal not in pos:
            return 0.0
        d_pix = math.hypot(pos[nid][0] - pos[goal][0], pos[nid][1] - pos[goal][1])
        return round((d_pix / max_span) * avg_w * 2.0, 2)

    g_score = {nid: math.inf for nid in node_ids}
    g_score[start_id] = 0.0
    parent = {}
    closed = []
    closed_set = set()
    tree_edges = []
    open_pq = [(h(start_id), 0.0, start_id)]

    steps = [
        _step(
            action="init",
            explanation=f"A* initialized from {start_id} toward goal {goal} using heuristic h(n).",
            visited=closed,
            frontier=[f"{start_id}(f={_fmt_dist(h(start_id))})"],
            frontier_label="Open Set f = g + h",
            current_node=start_id,
            distances={k: _fmt_dist(v) for k, v in g_score.items()},
        )
    ]

    while open_pq:
        f_val, g_val, u = heapq.heappop(open_pq)
        if u in closed_set:
            continue
        closed_set.add(u)
        closed.append(u)
        if u in parent:
            tree_edges.append((parent[u], u))

        steps.append(
            _step(
                action="expand",
                explanation=f"Expanded {u} with g={_fmt_dist(g_val)}, h={_fmt_dist(h(u))}, f={_fmt_dist(f_val)}.",
                visited=closed,
                frontier=[f"{n}(f={_fmt_dist(fv)})" for fv, _, n in sorted(open_pq) if n not in closed_set],
                frontier_label="Open Set f = g + h",
                current_node=u,
                active_edge=(parent[u], u) if u in parent else None,
                distances={k: _fmt_dist(v) for k, v in g_score.items()},
                tree_edges=tree_edges,
            )
        )

        if u == goal:
            break

        for v, w in adj[u]:
            if v in closed_set:
                continue
            tentative_g = g_val + w
            if tentative_g < g_score[v]:
                g_score[v] = tentative_g
                parent[v] = u
                f_next = tentative_g + h(v)
                heapq.heappush(open_pq, (f_next, tentative_g, v))
                steps.append(
                    _step(
                        action="update_open",
                        explanation=f"Queued {v} via {u}: g={_fmt_dist(tentative_g)}, h={_fmt_dist(h(v))}, f={_fmt_dist(f_next)}.",
                        visited=closed,
                        frontier=[f"{n}(f={_fmt_dist(fv)})" for fv, _, n in sorted(open_pq) if n not in closed_set],
                        frontier_label="Open Set f = g + h",
                        current_node=v,
                        active_edge=(u, v),
                        distances={k: _fmt_dist(v) for k, v in g_score.items()},
                        tree_edges=tree_edges,
                    )
                )

    path_nodes = _reconstruct_path(parent, start_id, goal)
    cost = _fmt_dist(g_score[goal]) if not math.isinf(g_score.get(goal, math.inf)) else None
    steps.append(
        _step(
            action="complete",
            explanation=(
                f"A* reached {goal}: {' -> '.join(path_nodes)} (g-cost {_fmt_dist(g_score[goal])})."
                if path_nodes
                else f"A* finished exploring toward {goal}."
            ),
            visited=closed,
            frontier=[],
            frontier_label="Open Set f = g + h",
            distances={k: _fmt_dist(v) for k, v in g_score.items()},
            tree_edges=tree_edges,
            path_nodes=path_nodes,
            total_weight=cost,
        )
    )
    return steps


def run_greedy_best_first(graph: dict, start_id: str, target_id=None, heuristics=None):
    node_ids, _, adj, pos = _build_adj(graph)
    if start_id not in adj:
        return [_step(action="error", explanation=f"Start node '{start_id}' not found.")]

    goal = target_id if (target_id and target_id in adj) else (node_ids[-1] if node_ids else start_id)
    custom_h = heuristics or {}

    def h(nid):
        if str(nid) in custom_h:
            try:
                return float(custom_h[str(nid)])
            except (ValueError, TypeError):
                pass
        if nid not in pos or goal not in pos:
            return 0.0
        return round(math.hypot(pos[nid][0] - pos[goal][0], pos[nid][1] - pos[goal][1]), 1)

    visited = []
    seen = set()
    parent = {}
    tree_edges = []
    pq = [(h(start_id), start_id)]
    h_map = {nid: h(nid) for nid in node_ids}

    steps = [
        _step(
            action="init",
            explanation=f"Greedy Best-First initialized from {start_id}, always picking lowest h(n) to {goal}.",
            visited=visited,
            frontier=[f"{start_id}(h={h(start_id)})"],
            frontier_label="Priority by h(n)",
            current_node=start_id,
            distances=h_map,
        )
    ]

    while pq:
        h_val, u = heapq.heappop(pq)
        if u in seen:
            continue
        seen.add(u)
        visited.append(u)
        if u in parent:
            tree_edges.append((parent[u], u))

        steps.append(
            _step(
                action="visit",
                explanation=f"Greedy pick: visited {u} with heuristic distance h={h_val} to {goal}.",
                visited=visited,
                frontier=[f"{n}(h={hv})" for hv, n in sorted(pq) if n not in seen],
                frontier_label="Priority by h(n)",
                current_node=u,
                active_edge=(parent[u], u) if u in parent else None,
                distances=h_map,
                tree_edges=tree_edges,
            )
        )

        if u == goal:
            break

        for v, _ in adj[u]:
            if v not in seen:
                parent[v] = u
                heapq.heappush(pq, (h(v), v))

    path_nodes = _reconstruct_path(parent, start_id, goal)
    steps.append(
        _step(
            action="complete",
            explanation=(
                f"Greedy Best-First path to {goal}: {' -> '.join(path_nodes)}."
                if path_nodes
                else f"Greedy Best-First finished from {start_id}."
            ),
            visited=visited,
            frontier=[],
            frontier_label="Priority by h(n)",
            distances=h_map,
            tree_edges=tree_edges,
            path_nodes=path_nodes,
        )
    )
    return steps


def run_tarjan_scc(graph: dict, start_id=None):
    node_ids, _, adj, _ = _build_adj(graph)
    if not node_ids:
        return [_step(action="error", explanation="Graph has no nodes.")]

    ordered_nodes = ([start_id] + [n for n in node_ids if n != start_id]) if start_id in adj else list(node_ids)
    index_counter = 0
    indices = {}
    lowlink = {}
    stack = []
    on_stack = set()
    visited_order = []
    sccs = []
    tree_edges = []

    steps = [
        _step(
            action="init",
            explanation="Tarjan's SCC initialized: tracking discovery index and low-link values.",
            visited=[],
            frontier=[],
            frontier_label="Tarjan Stack",
        )
    ]

    def strongconnect(u, parent_u=None):
        nonlocal index_counter
        indices[u] = index_counter
        lowlink[u] = index_counter
        index_counter += 1
        stack.append(u)
        on_stack.add(u)
        visited_order.append(u)

        steps.append(
            _step(
                action="discover",
                explanation=f"Node {u}: index={indices[u]}, lowlink={lowlink[u]}.",
                visited=visited_order,
                frontier=list(stack),
                frontier_label="Tarjan Stack",
                current_node=u,
                active_edge=(parent_u, u) if parent_u else None,
                distances={k: f"idx={indices[k]},low={lowlink[k]}" for k in indices},
                tree_edges=tree_edges,
            )
        )

        for v, _ in adj[u]:
            if v == parent_u:
                continue
            if v not in indices:
                tree_edges.append((u, v))
                strongconnect(v, u)
                lowlink[u] = min(lowlink[u], lowlink[v])
            elif v in on_stack:
                lowlink[u] = min(lowlink[u], indices[v])

        if lowlink[u] == indices[u]:
            comp = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                comp.append(w)
                if w == u:
                    break
            sccs.append(comp)
            steps.append(
                _step(
                    action="scc_found",
                    explanation=f"Formed component rooted at {u}: {{{', '.join(reversed(comp))}}}.",
                    visited=visited_order,
                    frontier=list(stack),
                    frontier_label="Tarjan Stack",
                    current_node=u,
                    distances={k: f"idx={indices[k]},low={lowlink[k]}" for k in indices},
                    tree_edges=tree_edges,
                    path_nodes=comp,
                )
            )

    for nid in ordered_nodes:
        if nid not in indices:
            strongconnect(nid)

    flat_scc = [n for comp in sccs for n in comp]
    steps.append(
        _step(
            action="complete",
            explanation=f"Tarjan pass complete: identified {len(sccs)} component(s).",
            visited=visited_order,
            frontier=[],
            frontier_label="Tarjan Stack",
            distances={k: f"idx={indices[k]},low={lowlink[k]}" for k in indices},
            tree_edges=tree_edges,
            path_nodes=flat_scc,
        )
    )
    return steps


def run_topological_sort(graph: dict, start_id=None):
    node_ids, clean_edges, _, _ = _build_adj(graph)
    if not node_ids:
        return [_step(action="error", explanation="Graph has no nodes.")]

    in_deg = {nid: 0 for nid in node_ids}
    dag_adj = {nid: [] for nid in node_ids}
    for u, v, _ in clean_edges:
        dag_adj[u].append(v)
        in_deg[v] += 1

    q = deque([nid for nid in node_ids if in_deg[nid] == 0])
    if start_id in q:
        q.remove(start_id)
        q.appendleft(start_id)

    topo = []
    steps = [
        _step(
            action="init",
            explanation="Topological Sort (Kahn's algorithm) initialized with zero-in-degree nodes.",
            visited=[],
            frontier=list(q),
            frontier_label="Zero In-Degree Queue",
            distances=dict(in_deg),
        )
    ]

    while q:
        u = q.popleft()
        topo.append(u)
        steps.append(
            _step(
                action="pop",
                explanation=f"Output {u} into topological ordering.",
                visited=topo,
                frontier=list(q),
                frontier_label="Zero In-Degree Queue",
                current_node=u,
                distances=dict(in_deg),
            )
        )
        for v in dag_adj[u]:
            in_deg[v] -= 1
            if in_deg[v] == 0:
                q.append(v)

    steps.append(
        _step(
            action="complete",
            explanation=f"Topological order ({len(topo)} nodes): {' -> '.join(topo)}.",
            visited=topo,
            frontier=[],
            frontier_label="Zero In-Degree Queue",
            distances=dict(in_deg),
            path_nodes=topo,
        )
    )
    return steps


def run_floyd_warshall(graph: dict, start_id=None, target_id=None):
    node_ids, clean_edges, _, _ = _build_adj(graph)
    if not node_ids:
        return [_step(action="error", explanation="Graph has no nodes.")]

    dist = {u: {v: (0.0 if u == v else math.inf) for v in node_ids} for u in node_ids}
    for u, v, w in clean_edges:
        dist[u][v] = min(dist[u][v], w)
        dist[v][u] = min(dist[v][u], w)

    src = start_id if start_id in dist else node_ids[0]
    steps = [
        _step(
            action="init",
            explanation=f"Floyd-Warshall initialized all-pairs matrix; inspecting row from {src}.",
            visited=[src],
            frontier=list(node_ids),
            frontier_label="Intermediate Pivots k",
            current_node=src,
            distances={v: _fmt_dist(dist[src][v]) for v in node_ids},
        )
    ]

    for k in node_ids:
        updated_any = False
        for i in node_ids:
            for j in node_ids:
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    if i == src:
                        updated_any = True
        steps.append(
            _step(
                action="pivot",
                explanation=f"Pivot k = {k}: updated shortest pairs where path through {k} is shorter.",
                visited=[n for n in node_ids if node_ids.index(n) <= node_ids.index(k)],
                frontier=[n for n in node_ids if node_ids.index(n) > node_ids.index(k)],
                frontier_label="Remaining Pivots k",
                current_node=k,
                distances={v: _fmt_dist(dist[src][v]) for v in node_ids},
            )
        )
        _ = updated_any

    cost = _fmt_dist(dist[src][target_id]) if (target_id and target_id in dist[src] and not math.isinf(dist[src][target_id])) else None
    steps.append(
        _step(
            action="complete",
            explanation=f"Floyd-Warshall complete across {len(node_ids)} vertices.",
            visited=list(node_ids),
            frontier=[],
            frontier_label="Remaining Pivots k",
            distances={v: _fmt_dist(dist[src][v]) for v in node_ids},
            path_nodes=[src, target_id] if (target_id and target_id in dist[src]) else list(node_ids),
            total_weight=cost,
        )
    )
    return steps


def run_cycle_detection(graph: dict, start_id=None):
    node_ids, clean_edges, adj, _ = _build_adj(graph)
    if not node_ids:
        return [_step(action="error", explanation="Graph has no nodes.")]

    parent = {nid: nid for nid in node_ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    visited = []
    seen = set()
    tree_edges = []
    cycles = []
    steps = [
        _step(
            action="init",
            explanation="Cycle Detection scanning edges with Disjoint Set (Union-Find).",
            visited=[],
            frontier=[f"{u}-{v}" for u, v, _ in clean_edges],
            frontier_label="Edges to Check",
        )
    ]

    for idx, (u, v, _) in enumerate(clean_edges):
        ru, rv = find(u), find(v)
        rem = [f"{a}-{b}" for a, b, _ in clean_edges[idx + 1:]]
        if ru != rv:
            parent[rv] = ru
            tree_edges.append((u, v))
            for x in (u, v):
                if x not in seen:
                    seen.add(x)
                    visited.append(x)
            steps.append(
                _step(
                    action="tree_edge",
                    explanation=f"Edge {u} — {v} joins separate components (acyclic).",
                    visited=visited,
                    frontier=rem,
                    frontier_label="Edges to Check",
                    current_node=v,
                    active_edge=(u, v),
                    tree_edges=tree_edges,
                )
            )
        else:
            cycles.append((u, v))
            steps.append(
                _step(
                    action="cycle_found",
                    explanation=f"Cycle detected! Edge {u} — {v} connects two nodes already in component {ru}.",
                    visited=visited,
                    frontier=rem,
                    frontier_label="Edges to Check",
                    current_node=u,
                    active_edge=(u, v),
                    tree_edges=tree_edges,
                    path_nodes=[u, v],
                )
            )

    steps.append(
        _step(
            action="complete",
            explanation=(
                f"Found {len(cycles)} cycle-closing edge(s): {', '.join(f'{a}-{b}' for a, b in cycles)}."
                if cycles
                else "No cycles detected; graph is acyclic (a forest)."
            ),
            visited=visited,
            frontier=[],
            frontier_label="Edges to Check",
            tree_edges=tree_edges,
            total_weight=len(cycles),
        )
    )
    return steps


def run_algorithm(graph: dict, algorithm: str, start_id: str, target_id=None, heuristics=None):
    algo = (algorithm or "Dijkstra").strip().lower()
    if algo in ("dijkstra", "dijkstra's shortest path"):
        return run_dijkstra(graph, start_id, target_id=target_id)
    if algo in ("bellman-ford", "bellman ford", "bellman_ford"):
        return run_bellman_ford(graph, start_id, target_id=target_id)
    if algo in ("prim's mst", "prims", "prim"):
        return run_prims(graph, start_id)
    if algo in ("kruskal's mst", "kruskal", "kruskals"):
        return run_kruskal(graph, start_id=start_id)
    if algo in ("a*", "astar", "a star"):
        return run_astar(graph, start_id, target_id=target_id, heuristics=heuristics)
    if algo in ("greedy best-first", "greedy", "best-first", "greedy first"):
        return run_greedy_best_first(graph, start_id, target_id=target_id, heuristics=heuristics)
    if algo in ("tarjan", "tarjan scc", "tarjan's scc", "scc"):
        return run_tarjan_scc(graph, start_id=start_id)
    if algo in ("topological sort", "topo", "toposort"):
        return run_topological_sort(graph, start_id=start_id)
    if algo in ("floyd-warshall", "floyd warshall", "floyd"):
        return run_floyd_warshall(graph, start_id=start_id, target_id=target_id)
    if algo in ("cycle detection", "cycle"):
        return run_cycle_detection(graph, start_id=start_id)
    if algo == "dfs":
        return run_dfs(graph, start_id)
    return run_bfs(graph, start_id)