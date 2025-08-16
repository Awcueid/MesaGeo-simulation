import networkx as nx
import matplotlib.pyplot as plt
from model import Main_model

def visualize_network():
    # Create an instance of the model
    model = Main_model()
    
    # Create a new figure with interactive features
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Get positions for nodes (using the actual coordinates from the graph)
    pos = {node: (node[0], node[1]) for node in model.road_graph.nodes()}
    
    # Draw only the nodes
    node_x = [x for x, y in pos.values()]
    node_y = [y for x, y in pos.values()]
    ax.scatter(node_x, node_y, c='blue', s=20, alpha=0.6, label='Road Nodes')
    
    plt.title('Road Network Nodes')
    plt.legend()
    
    # Enable equal aspect ratio
    ax.set_aspect('equal')
    
    # Enable zoom and pan
    plt.gcf().canvas.manager.set_window_title('Road Network Viewer (Use mouse wheel to zoom)')
    
    # Add instructions text
    plt.figtext(0.02, 0.02, 'Mouse wheel: Zoom\nClick and drag: Pan', 
                fontsize=8, bbox=dict(facecolor='white', alpha=0.7))
    
    plt.show()

if __name__ == "__main__":
    visualize_network()
