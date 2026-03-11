import random
import networkx as nx
import mesa_geo as mg
from shapely.geometry import Point

class Car_agent(mg.GeoAgent):
    """Create a new car agent"""

    def __init__(self, model, geometry, crs, speed=1):
        super().__init__(model, geometry, crs)

        # List of points to visit
        self.path = []
        self.current_index = 0
        self.speed = speed
        self.speed_factor = 1.0  

        # intial path planning
        start_node = self.nearest_node(self.geometry)
        end_node = random.choice(list(self.model.road_graph.nodes))
        self.plan_path(start_node, end_node)

    def plan_path(self, start, end):
        try:
            # Find the shortest path
            self.path = nx.shortest_path( 
                self.model.road_graph,
                source=start,
                target=end,
                weight="weight"
            )
            self.current_index = 0
        except nx.NetworkXNoPath:
            self.path = []
    
    def nearest_node(self, point): 
        """Find the nearest node in the road graph"""
        nodes = list(self.model.road_graph.nodes)
        return min(nodes, key=lambda n: point.distance(Point(n)))

    def step(self):
        """Advance car agent one step using directed-lane occupancy"""

        # If no path or at end, (re)plan
        if self.current_index >= len(self.path) - 1:
            start_node = self.nearest_node(self.geometry)
            end_node = random.choice(list(self.model.road_graph.nodes))
            self.plan_path(start_node, end_node)
            if not self.path:
                return

        # 1 step = 1 second, node spacing = 5 m  =>  nodes/step = speed_kmh * factor / 3.6 / 5
        u0 = self.path[self.current_index]
        v0 = self.path[self.current_index + 1]
        edge_data = self.model.road_graph.get_edge_data(u0, v0)
        first_edge = next(iter(edge_data.values()), {}) if edge_data else {}
        speed_kmh = first_edge.get("speed_kmh", 40.0)
        moves_allowed = max(1, round(speed_kmh * self.speed_factor / 3.6 / 5))

        steps_done = 0
        while steps_done < moves_allowed and self.current_index < len(self.path) - 1:
            u = self.path[self.current_index]
            v = self.path[self.current_index + 1]

            edge_data = self.model.road_graph.get_edge_data(u, v)
            seg_lanes = next(iter(edge_data.values()), {}).get("num_lanes", 1) if edge_data else 1

            # Fast drivers (speed_factor >= 1.0) prefer outer lanes — overtaking.
            # Slow drivers keep to inner lane 0 — keep right.
            lane_order = reversed(range(seg_lanes)) if self.speed_factor >= 1.0 else range(seg_lanes)

            moved = False
            for lane in lane_order:
                key = (u, v, lane)
                if key not in self.model.car_lane_occupancy:
                    self.model.car_lane_occupancy[key] = self
                    self.current_index += 1
                    self.geometry = Point(v)
                    self.model.car_lane_occupancy.pop(key, None)
                    steps_done += 1
                    moved = True
                    break

            if not moved:
                # Blocked on all lanes for this edge this tick
                break

class test_car(mg.GeoAgent):
    """Agent that moves from road a to b to determine time to travel"""

    def __init__(self, model, geometry, crs, speed=1):
        super().__init__(model, geometry, crs)

        start_node = -8965387.52181617, 5387148.721794528  # starting at the north most point
        end_node = -8968572.588849764, 5383403.789376198   # ending at the south most point
        self.speed = speed
        self.path = []
        self.current_index = 0
        self.travel_time = 0
        self.finished = False
        self.plan_path(start_node, end_node)

    def plan_path(self, start, end):
        try:
            # Find the shortest path
            self.path = nx.shortest_path(
                self.model.road_graph,
                source=start,
                target=end,
                weight="weight"
            )
            self.current_index = 0
        except nx.NetworkXNoPath:
            self.path = []
            self.finished = True

    def step(self):
        if self.finished or not self.path:
            return

        # Read speed limit from the next edge (nodes/step = speed_kmh * factor / 3.6 / 5)
        u0 = self.path[self.current_index]
        v0 = self.path[self.current_index + 1]
        edge_data = self.model.road_graph.get_edge_data(u0, v0)
        first_edge = next(iter(edge_data.values()), {}) if edge_data else {}
        speed_kmh = first_edge.get("speed_kmh", 40.0)
        moves_allowed = max(1, round(speed_kmh * self.speed_factor / 3.6 / 5))

        moves = 0
        while moves < moves_allowed and self.current_index < len(self.path) - 1:
            u = self.path[self.current_index]
            v = self.path[self.current_index + 1]

            edge_data = self.model.road_graph.get_edge_data(u, v)
            seg_lanes = next(iter(edge_data.values()), {}).get("num_lanes", 1) if edge_data else 1

            # test_car drives exactly at the limit (speed_factor = 1.0) — use outer lanes
            lane_order = reversed(range(seg_lanes))

            moved = False
            for lane in lane_order:
                key = (u, v, lane)
                if key not in self.model.car_lane_occupancy:
                    self.model.car_lane_occupancy[key] = self
                    self.current_index += 1
                    self.geometry = Point(v)
                    self.model.car_lane_occupancy.pop(key, None)
                    moved = True
                    moves += 1
                    break

            if not moved:
                break

        self.travel_time += 1

        if self.current_index == len(self.path) - 1:
            self.finished = True
            print(f"Test car reached destination in {self.travel_time} steps.")