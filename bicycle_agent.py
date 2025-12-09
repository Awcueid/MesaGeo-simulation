import random
import networkx as nx
import mesa_geo as mg
from shapely.geometry import Point


class Bicycle_agent(mg.GeoAgent):
    """Simple bicycle agent moving along road graph"""

    def __init__(self, model, geometry, crs, speed=1):
        super().__init__(model, geometry, crs)

        self.path = []
        self.current_index = 0
        self.speed = speed

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
        if self.current_index >= len(self.path) - 1:
            start_node = self.nearest_node(self.geometry)
            end_node = random.choice(list(self.model.road_graph.nodes))
            self.plan_path(start_node, end_node)
            if not self.path:
                return

        steps_done = 0
        while steps_done < self.speed and self.current_index < len(self.path) - 1:
            u = self.path[self.current_index]
            v = self.path[self.current_index + 1]

            moved = False
            # Prefer side lanes: highest index first to keep away from cars
            for lane in reversed(range(self.model.road_lanes)):
                key = (u, v, lane)
                if key not in self.model.bicycle_lane_occupancy:
                    self.model.bicycle_lane_occupancy[key] = self
                    self.current_index += 1
                    self.geometry = Point(v)
                    self.model.bicycle_lane_occupancy.pop(key, None)
                    steps_done += 1
                    moved = True
                    break

            if not moved:
                break


class test_bicycle(mg.GeoAgent):
    """Test bicycle agent moving from fixed start to end to compare travel time"""

    def __init__(self, model, geometry, crs, speed=1):
        super().__init__(model, geometry, crs)

        start_node = -8965387.52181617, 5387148.721794528
        end_node = -8968572.588849764, 5383403.789376198

        self.speed = speed
        self.path = []
        self.current_index = 0
        self.travel_time = 0
        self.finished = False
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
            self.finished = True

    def step(self):
        if self.finished or not self.path:
            return

        moves = 0
        while moves < self.speed and self.current_index < len(self.path) - 1:
            u = self.path[self.current_index]
            v = self.path[self.current_index + 1]

            moved = False
            
            # use side lanes
            for lane in reversed(range(self.model.road_lanes)):
                key = (u, v, lane)
                if key not in self.model.bicycle_lane_occupancy:
                    self.model.bicycle_lane_occupancy[key] = self
                    self.current_index += 1
                    self.geometry = Point(v)
                    self.model.bicycle_lane_occupancy.pop(key, None)
                    moved = True
                    moves += 1
                    break

            if not moved:
                break

        self.travel_time += 1

        if self.current_index == len(self.path) - 1:
            self.finished = True
            print(f"Test bicycle reached destination in {self.travel_time} steps.")
