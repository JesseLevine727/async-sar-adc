#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import math
import random
import re

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
DOT_PATH = ROOT / "sar_logic_synth.dot"
OUT_PATH = ROOT / "sar_logic_synth_preview.png"

NODE_RE = re.compile(r'^\s*([A-Za-z0-9_]+)\s+\[\s*(.+?)\s*\];\s*$')
EDGE_RE = re.compile(r'^\s*([A-Za-z0-9_]+)(?::[^\s]+)?\s*->\s*([A-Za-z0-9_]+)(?::[^\s]+)?')
LABEL_RE = re.compile(r'label="([^"]*)"')
SHAPE_RE = re.compile(r'shape=([A-Za-z0-9_]+)')


def parse_dot(path: Path):
    nodes = {}
    edges = []
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        node_match = NODE_RE.match(line)
        if node_match:
            node_id, attrs = node_match.groups()
            label_match = LABEL_RE.search(attrs)
            shape_match = SHAPE_RE.search(attrs)
            nodes[node_id] = {
                "label": label_match.group(1) if label_match else node_id,
                "shape": shape_match.group(1) if shape_match else "ellipse",
            }
            continue

        edge_match = EDGE_RE.match(line)
        if edge_match:
            src, dst = edge_match.groups()
            edges.append((src, dst))

    return nodes, edges


def node_kind(node_id: str, meta: dict[str, str]) -> str:
    if node_id.startswith("c"):
        return "cell"
    if node_id.startswith("x"):
        return "slice"
    if meta["shape"] == "octagon":
        return "port"
    if meta["shape"] == "diamond":
        return "state"
    return "other"


def initial_positions(nodes: dict[str, dict[str, str]]):
    groups = {"port": [], "state": [], "cell": [], "slice": [], "other": []}
    for node_id, meta in nodes.items():
        groups[node_kind(node_id, meta)].append(node_id)

    x_map = {"port": 0.0, "state": 1.2, "cell": 2.8, "slice": 4.4, "other": 5.2}
    pos = {}
    for group_name, node_ids in groups.items():
        node_ids.sort()
        n = max(len(node_ids), 1)
        for idx, node_id in enumerate(node_ids):
            y = 1.0 - 2.0 * (idx + 0.5) / n
            pos[node_id] = [x_map[group_name], y]
    return pos


def fruchterman_reingold(nodes, edges, pos, iterations=250):
    ids = list(nodes.keys())
    n = max(len(ids), 1)
    area = 16.0
    k = math.sqrt(area / n)
    random.seed(5705)

    adjacency = {node_id: set() for node_id in ids}
    for a, b in edges:
        if a in adjacency and b in adjacency:
            adjacency[a].add(b)
            adjacency[b].add(a)

    for _ in range(iterations):
        disp = {node_id: [0.0, 0.0] for node_id in ids}

        for i, v in enumerate(ids):
            for u in ids[i + 1 :]:
                dx = pos[v][0] - pos[u][0]
                dy = pos[v][1] - pos[u][1]
                dist = math.hypot(dx, dy) + 1e-6
                force = (k * k) / dist
                rx = dx / dist * force
                ry = dy / dist * force
                disp[v][0] += rx
                disp[v][1] += ry
                disp[u][0] -= rx
                disp[u][1] -= ry

        for v, nbrs in adjacency.items():
            for u in nbrs:
                if v >= u:
                    continue
                dx = pos[v][0] - pos[u][0]
                dy = pos[v][1] - pos[u][1]
                dist = math.hypot(dx, dy) + 1e-6
                force = (dist * dist) / k
                ax = dx / dist * force
                ay = dy / dist * force
                disp[v][0] -= ax
                disp[v][1] -= ay
                disp[u][0] += ax
                disp[u][1] += ay

        for node_id in ids:
            kind = node_kind(node_id, nodes[node_id])
            step = 0.04 if kind == "slice" else 0.08
            disp_len = math.hypot(disp[node_id][0], disp[node_id][1]) + 1e-9
            pos[node_id][0] += disp[node_id][0] / disp_len * min(step, disp_len)
            pos[node_id][1] += disp[node_id][1] / disp_len * min(step, disp_len)

            if kind == "port":
                pos[node_id][0] = min(pos[node_id][0], 0.35)
            elif kind == "state":
                pos[node_id][0] = min(max(pos[node_id][0], 0.8), 1.8)
            elif kind == "cell":
                pos[node_id][0] = min(max(pos[node_id][0], 1.8), 3.6)
            elif kind == "slice":
                pos[node_id][0] = min(max(pos[node_id][0], 3.4), 4.8)

            pos[node_id][1] = min(max(pos[node_id][1], -1.25), 1.25)

    return pos


def short_label(node_id: str, meta: dict[str, str]) -> str:
    label = meta["label"].replace("\\n", "\n")
    if node_id.startswith("c"):
        parts = label.split("\n")
        return parts[-1] if parts else node_id
    if node_id.startswith("x"):
        return ""
    return label


def render(nodes, edges, pos, out_path: Path):
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_facecolor("white")

    for src, dst in edges:
        if src not in pos or dst not in pos:
            continue
        sx, sy = pos[src]
        dx, dy = pos[dst]
        ax.annotate(
            "",
            xy=(dx, dy),
            xytext=(sx, sy),
            arrowprops=dict(arrowstyle="-", color="#9aa1a8", lw=0.5, alpha=0.35),
        )

    style = {
        "port": dict(color="#0f766e", size=250, marker="o"),
        "state": dict(color="#2563eb", size=280, marker="D"),
        "cell": dict(color="#b45309", size=120, marker="s"),
        "slice": dict(color="#6b7280", size=30, marker="o"),
        "other": dict(color="#374151", size=120, marker="o"),
    }

    for node_id, meta in nodes.items():
        kind = node_kind(node_id, meta)
        cfg = style[kind]
        x, y = pos[node_id]
        ax.scatter([x], [y], s=cfg["size"], c=cfg["color"], marker=cfg["marker"], zorder=3)
        label = short_label(node_id, meta)
        if label:
            fs = 7 if kind == "cell" else 9
            dx = 0.02 if kind != "cell" else 0.04
            ax.text(x + dx, y, label, fontsize=fs, va="center", ha="left", color="#111827")

    ax.set_title("Synthesized SAR Controller Structural Graph", fontsize=14)
    ax.text(
        0.0,
        -1.42,
        "Ports: teal   State/storage: blue   Logic cells: brown   Bit-slice connectors: gray",
        fontsize=10,
        color="#374151",
    )
    ax.set_xlim(-0.2, 5.1)
    ax.set_ylim(-1.5, 1.35)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main():
    nodes, edges = parse_dot(DOT_PATH)
    pos = initial_positions(nodes)
    pos = fruchterman_reingold(nodes, edges, pos)
    render(nodes, edges, pos, OUT_PATH)
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()
