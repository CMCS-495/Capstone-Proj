import json
import os
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyBboxPatch
import numpy as np

def load_rooms(json_path):
    with open(json_path, 'r') as f:
        return json.load(f)

def build_graph(rooms):
    G = nx.Graph()
    for room in rooms:
        rid = room['room_id']
        G.add_node(rid, **room)
        for nbr in room.get('neighbors', []):
            G.add_edge(rid, nbr)
    return G

def compute_positions(G, scale=1):
    init_pos, fixed = {}, []
    for n, data in G.nodes(data=True):
        if 'MiniMapX' in data and 'MiniMapy' in data:
            init_pos[n] = (data['MiniMapX'], data['MiniMapy'])
            fixed.append(n)
    if init_pos:
        return nx.spring_layout(G, pos=init_pos, fixed=fixed, scale=scale, seed=42)
    else:
        return nx.spring_layout(G, scale=scale, seed=42)

def draw_tree(ax, x, y, w, h, orientation):
    if orientation == 'inward':
        pts = [(x, y), (x + w, y - h/2), (x + w, y + h/2)]
    elif orientation == 'outward':
        pts = [(x, y), (x - w, y - h/2), (x - w, y + h/2)]
    elif orientation == 'top':
        pts = [(x, y), (x - w/2, y - h), (x + w/2, y - h)]
    else:  # bottom
        pts = [(x, y), (x - w/2, y + h), (x + w/2, y + h)]
    tri = Polygon(pts, closed=True, facecolor='green', edgecolor='darkgreen', zorder=0)
    ax.add_patch(tri)

def draw_map(json_path,
             discovered_rooms,
             output_file='map.png',
             title='Dungeon Map'):
    # load + layout
    rooms = load_rooms(json_path)
    G     = build_graph(rooms)
    pos   = compute_positions(G, scale=1)

    # setup fig
    fig, ax = plt.subplots(figsize=(8,8))
    fig.patch.set_facecolor('#F5F5DC')
    ax.set_facecolor('#F5F5DC')
    ax.axis('off')

    # compute bounds
    xs = np.array([p[0] for p in pos.values()])
    ys = np.array([p[1] for p in pos.values()])
    min_x, max_x = xs.min(), xs.max()
    min_y, max_y = ys.min(), ys.max()
    mx = (max_x - min_x)*0.2
    my = (max_y - min_y)*0.2
    left, right   = min_x - mx, max_x + mx
    bottom, top   = min_y - my, max_y + my
    tree_w = (right - left)*0.03
    tree_h = (top - bottom)*0.05

    # draw border trees
    count = 20
    for y in np.linspace(bottom, top, count):
        draw_tree(ax, left,  y, tree_w, tree_h, 'inward')
        draw_tree(ax, right, y, tree_w, tree_h, 'outward')
    for x in np.linspace(left, right, count):
        draw_tree(ax, x, top,    tree_w, tree_h, 'top')
        draw_tree(ax, x, bottom, tree_w, tree_h, 'bottom')

    # draw discovered edges
    for u, v in G.edges():
        if u in discovered_rooms and v in discovered_rooms:
            x0,y0 = pos[u]; x1,y1 = pos[v]
            ax.plot([x0,x1], [y0,y1],
                    linewidth=10, solid_capstyle='round',
                    color='#8B4513', alpha=0.7, zorder=1)

    # parameters for node & label
    node_radius   = 0.03
    label_gap     = 0.015   # extra space between circle and text
    offset_dist   = node_radius + label_gap

    # draw nodes + smart labels
    for n in discovered_rooms:
        if n not in pos: continue
        x,y = pos[n]

        # draw the room circle
        circ = plt.Circle((x,y), node_radius,
                          facecolor='saddlebrown',
                          edgecolor='black',
                          linewidth=1, zorder=2)
        ax.add_patch(circ)

        # compute offset direction
        neighs = [nbr for nbr in G.neighbors(n) if nbr in discovered_rooms]
        if neighs:
            vecs = [np.array(pos[nbr]) - np.array([x,y]) for nbr in neighs]
            avg  = sum(vecs) / len(vecs)
            disp = -avg
            if np.allclose(disp, 0):
                disp = np.array([0,1])
        else:
            disp = np.array([0,1])  # no edges → place above

        unit = disp / np.linalg.norm(disp)
        lx, ly = np.array([x,y]) + unit * offset_dist

        # draw the label text just off the node, away from paths
        name = G.nodes[n].get('name', n)
        ax.text(lx, ly, name,
                fontsize=8, fontfamily='serif',
                zorder=5)

    # draw the scroll title
    sw = (right-left)*0.5
    sh = (top-bottom)*0.1
    sx = (left+right)/2 - sw/2
    sy = top + my*0.1
    scroll = FancyBboxPatch((sx, sy), sw, sh,
                            boxstyle="round,pad=0.1",
                            edgecolor='saddlebrown',
                            facecolor='cornsilk',
                            linewidth=2, zorder=3)
    ax.add_patch(scroll)
    ax.text(sx + sw/2, sy + sh/2,
            title, ha='center', va='center',
            fontsize=16, fontfamily='serif', zorder=4)

    # finalize & save
    ax.set_xlim(left - tree_w, right + tree_w)
    ax.set_ylim(bottom - tree_h, sy + sh + my*0.05)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f"Map saved to {output_file}")

if __name__ == '__main__':
    # example: only these rooms have been discovered so far
    discovered = {'R1_1', 'R1_2', 'R1_4', 'R2_1'}
    # point this at wherever your map.json lives
    map_file = os.path.join(os.path.dirname(__file__),'Game_Assets', 'map.json')
    draw_map(map_file, discovered, output_file='partial_map.png',title='Mini Map')
