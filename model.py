import geopandas as gpd
import networkx as nx
import mesa
import random
import mesa_geo as mg
from shapely.geometry import LineString, Point
from datetime import datetime, timedelta

class test_agent(mg.GeoAgent):
    """Agent that moves from road a to b to determine time to travel"""
    
    def __init__(self, model, geometry, crs, speed=1, ):
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
        moves = 0
        while moves < self.speed and self.current_index < len(self.path) - 1:
            u = self.path[self.current_index]
            v = self.path[self.current_index + 1]

            # Try default lane 0 first, then others if available
            moved = False
            for lane in range(self.model.road_lanes):
                key = (u, v, lane)
                if key not in self.model.lane_occupancy:
                    # Reserve, move, then release immediately (discrete hop)
                    self.model.lane_occupancy[key] = self
                    self.current_index += 1
                    self.geometry = Point(v)
                    self.model.lane_occupancy.pop(key, None)
                    moved = True
                    moves += 1
                    break

            if not moved:
                # Blocked on all lanes for this directed edge; stop this tick
                break

        # track travel time
        self.travel_time += 1

        if self.current_index == len(self.path) - 1:
            self.finished = True
            print(f"Test agent reached destination in {self.travel_time} steps.")
                

class Car_agent(mg.GeoAgent):
    """Create a new car agent"""

    def __init__(self, model, geometry, crs, speed=1):
        super().__init__(model, geometry, crs)

        # List of points to visit
        self.path = []
        self.current_index = 0
        self.speed = speed

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

        # Move in increments of one node up to 'speed'
        steps_done = 0
        while steps_done < self.speed and self.current_index < len(self.path) - 1:
            u = self.path[self.current_index]
            v = self.path[self.current_index + 1]

            moved = False
            # Preferred lane first (0), then others
            for lane in range(self.model.road_lanes):
                key = (u, v, lane)
                if key not in self.model.lane_occupancy:
                    self.model.lane_occupancy[key] = self
                    # perform move
                    self.current_index += 1
                    self.geometry = Point(v)
                    # release occupancy immediately after move
                    self.model.lane_occupancy.pop(key, None)
                    steps_done += 1
                    moved = True
                    break

            if not moved:
                # Blocked on this directed edge across all lanes this tick
                break


def interpolate_linestring(line: LineString, spacing=5):
    """Helper function for points"""
    return [line.interpolate(distance) 
        for distance in range(0, int(line.length), spacing)] + [line.interpolate(line.length)]


class Main_model(mesa.Model):
    """Main model class for the neighborhood project"""

    def __init__(self, num_of_cars=100, speed_limit=40, road_lanes=1):
        super().__init__()
        
        self.start_time = datetime.now()
        self.sim_time = timedelta(seconds=0)
        self.space = mg.GeoSpace(warn_crs_conversion=False)
        self.running = True
        self.speed_limit = speed_limit
        self.road_lanes = road_lanes
        self.lane_occupancy: dict[tuple, object] = {}

        # read in the geojson files
        road_path = "Maps/Roads.geojson"
        buildings_path = "Maps/Buildings.geojson"

        # Set up roads
        roads_comp = gpd.read_file(road_path).to_crs(epsg=3857)
        road_agents = [mg.GeoAgent(self, geometry=geom, crs=roads_comp.crs) for geom in roads_comp.geometry]
        self.space.add_agents(road_agents)

        # Set up buildings
        buildings_comp = gpd.read_file(buildings_path).to_crs(epsg=3857)
        buildings_agents = [mg.GeoAgent(self, geometry=geom, crs=buildings_comp.crs) for geom in buildings_comp.geometry]
        self.space.add_agents(buildings_agents)
        
        # Create a road graph from the roads
        # Build a directed multigraph where parallel edges represent lanes
        self.road_graph = nx.MultiDiGraph()
        spacing = 5  # meters between points
        for i, row in roads_comp.iterrows():
            line = row.geometry
            points = interpolate_linestring(line, spacing)
            #coords = list(row.geometry.coords)
            for start, end in zip(points[:-1], points[1:]):
                start_xy = (start.x, start.y)
                end_xy = (end.x, end.y)
                dist = Point(start_xy).distance(Point(end_xy))
                # add lanes for both directions as parallel edges
                for lane in range(self.road_lanes):
                    # forward lane
                    self.road_graph.add_edge(
                        start_xy,
                        end_xy,
                        key=lane,
                        weight=dist,
                        lane=lane,
                        direction=1,
                    )
                    # backward lane
                    self.road_graph.add_edge(
                        end_xy,
                        start_xy,
                        key=lane,
                        weight=dist,
                        lane=lane,
                        direction=-1,
                    )

        # Set up cars
        car_ac = mg.AgentCreator(Car_agent, model=self,crs="EPSG:3857") # set crs because it breaks otherwise
        car_agents = []
        nodes = list(self.road_graph.nodes) # Get all nodes from the road graph
        for i in range(num_of_cars):  
            # Create car agents with random positions 
            start_node = random.choice(nodes)
            car_agent = car_ac.create_agent(
                geometry=Point(start_node),
            )
            car_agent.speed = 2  # Speed for 40km/h = 11.11m/s ≈ 2.22 nodes (rounded to 2 nodes per step since nodes are 5m apart)
            car_agents.append(car_agent)
        self.space.add_agents(car_agents)

        # Track car agents
        self.cars = [
            agent for agent in self.space.agents if callable(getattr(agent, "step", None))
        ]
        
        northmost = max(nodes, key=lambda n: n[1])
        #southmost = min(nodes, key=lambda n: n[1])


        test_ac = mg.AgentCreator(test_agent, model=self, crs="EPSG:3857")
        test_car = test_ac.create_agent(
            geometry=Point(northmost),
        )
        test_car.speed = 2  # Speed for 40km/h = 11.11m/s ≈ 2.22 nodes (rounded to 2 nodes per step since nodes are 5m apart)

        # add the test car to the space and cars list
        self.space.add_agents([test_car])
        self.cars.append(test_car)

        # debug
        #print("roads_comp.crs:", roads_comp.crs)
        #print("Point(start_node):", Point(start_node))

    def step(self):
        """Run one step of the model"""
        self.sim_time += timedelta(seconds=1)
        
        for agent in self.cars:
            agent.step()