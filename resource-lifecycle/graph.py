import matplotlib.pyplot as plt
import networkx as nx

# Create a directed graph
G = nx.DiGraph()

# Define the steps as nodes
steps = [
    "User Requests Resource",
    "Estimate Cost",
    "Compare with Average Monthly Cost",
    "Request Approval if >= 10%",
    "Create Resource if < 10%",
    "Schedule Follow-up in a Week",
    "Ask Developer to Keep or Delete Resource",
    "Keep Resource and Schedule Next Follow-up",
    "Delete Resource",
    "Communicate Decision to Developer",
    "Suggest Better-Fit Resources/Services"
]

# Add the nodes to the graph
for step in steps:
    G.add_node(step)

# Define the edges with operations
edges = [
    ("User Requests Resource", "Estimate Cost"),
    ("Estimate Cost", "Compare with Average Monthly Cost"),
    ("Compare with Average Monthly Cost", "Request Approval if >= 10%"),
    ("Compare with Average Monthly Cost", "Create Resource if < 10%"),
    ("Create Resource if < 10%", "Schedule Follow-up in a Week"),
    ("Schedule Follow-up in a Week", "Ask Developer to Keep or Delete Resource"),
    ("Ask Developer to Keep or Delete Resource", "Keep Resource and Schedule Next Follow-up"),
    ("Ask Developer to Keep or Delete Resource", "Delete Resource"),
    ("Keep Resource and Schedule Next Follow-up", "Schedule Follow-up in a Week"),
    ("Create Resource if < 10%", "Communicate Decision to Developer"),
    ("Estimate Cost", "Suggest Better-Fit Resources/Services"),
    ("Suggest Better-Fit Resources/Services", "Communicate Decision to Developer")
]

# Add the edges to the graph
for edge in edges:
    G.add_edge(*edge)

# Manually define the positions for the nodes with more spacing
pos = {
    "User Requests Resource": (0, 10),
    "Estimate Cost": (2, 10),
    "Compare with Average Monthly Cost": (4, 10),
    "Request Approval if >= 10%": (6, 12),
    "Create Resource if < 10%": (6, 8),
    "Schedule Follow-up in a Week": (8, 8),
    "Ask Developer to Keep or Delete Resource": (10, 8),
    "Keep Resource and Schedule Next Follow-up": (12, 10),
    "Delete Resource": (12, 6),
    "Communicate Decision to Developer": (8, 4),
    "Suggest Better-Fit Resources/Services": (4, 4)
}

# Adjust the figure size
plt.figure(figsize=(18, 12))

# Draw the nodes
nx.draw_networkx_nodes(G, pos, node_size=3000, node_color='skyblue', alpha=0.9)

# Draw the edges
nx.draw_networkx_edges(G, pos, edgelist=edges, arrowstyle='-|>', arrowsize=20, edge_color='gray')

# Draw the labels
nx.draw_networkx_labels(G, pos, font_size=12, font_color='black', font_weight='bold')

# Draw the edge labels with simplified text
edge_labels = {
    ("User Requests Resource", "Estimate Cost"): "Start",
    ("Estimate Cost", "Compare with Average Monthly Cost"): "",
    ("Compare with Average Monthly Cost", "Request Approval if >= 10%"): ">= 10%",
    ("Compare with Average Monthly Cost", "Create Resource if < 10%"): "< 10%",
    ("Create Resource if < 10%", "Schedule Follow-up in a Week"): "",
    ("Schedule Follow-up in a Week", "Ask Developer to Keep or Delete Resource"): "",
    ("Ask Developer to Keep or Delete Resource", "Keep Resource and Schedule Next Follow-up"): "Keep",
    ("Ask Developer to Keep or Delete Resource", "Delete Resource"): "Delete",
    ("Keep Resource and Schedule Next Follow-up", "Schedule Follow-up in a Week"): "Repeat",
    ("Create Resource if < 10%", "Communicate Decision to Developer"): "",
    ("Estimate Cost", "Suggest Better-Fit Resources/Services"): "Alternative",
    ("Suggest Better-Fit Resources/Services", "Communicate Decision to Developer"): ""
}

nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red')

# Set the plot title
plt.title("Intelligent Agent Workflow for AWS Resource Management", fontsize=16, fontweight='bold')

# Display the graph
plt.show()
