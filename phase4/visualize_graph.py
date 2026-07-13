import sys
import os
sys.path.append(os.path.dirname(__file__))

from graph import build_graph
from PIL import Image
import io

app = build_graph()

# Generate graph as PNG image
graph_image = app.get_graph().draw_mermaid_png()

# Save it
with open("agent_graph.png", "wb") as f:
    f.write(graph_image)

print("✅ Graph saved as agent_graph.png")