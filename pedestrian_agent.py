import random
import networkx as nx
import mesa_geo as mg
from shapely.geometry import Point


class Pedestrian_agent(mg.GeoAgent):
    """Simple pedestrian agent moving slowly along the road graph"""

    def __init__(self, model, geometry, crs, speed=1):
        super().__init__(model, geometry, crs)

        self.path = []
        self.current_index = 0
        self.speed = speed
        self.step_count = 0

        start_node = self.nearest_node(self.geometry)
        end_node = random.choice(list(self.model.road_graph.nodes))
        self.plan_path(start_node, end_node)

    def plan_path(self, start, end):
        try:
            self.path = nx.shortest_path(
                self.model.road_graph,
                source=start,
                target=end,
                weight="weight",
            )
            self.current_index = 0
        except nx.NetworkXNoPath:
            self.path = []

    def nearest_node(self, point):
        nodes = list(self.model.road_graph.nodes)
        return min(nodes, key=lambda n: point.distance(Point(n)))

    def step(self):
        # move only every second model step
        self.step_count += 1
        if self.step_count % 2 != 0:
            return

        if self.current_index >= len(self.path) - 1:
            start_node = self.nearest_node(self.geometry)
            end_node = random.choice(list(self.model.road_graph.nodes))
            self.plan_path(start_node, end_node)
            if not self.path:
                return

        # move exactly one node when it is a movement step
        if self.current_index < len(self.path) - 1:
            u = self.path[self.current_index]
            v = self.path[self.current_index + 1]
            self.current_index += 1
            self.geometry = Point(v)
