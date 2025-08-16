import geopandas as gpd
import networkx as nx
import mesa
import random
import mesa_geo as mg
from mesa_geo import AgentCreator
from shapely.geometry import LineString, Point
from datetime import datetime, timedelta


def get_blocking_cars(space, next_pos, self_agent, agent_type):
    """Returns list of agents blocking next position"""
    return [
        agent for agent in space.agents
        if isinstance(agent, agent_type)
        and agent != self_agent
        and tuple(agent.geometry.coords[0]) == tuple(next_pos)
    ]


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
        if self.current_index < len(self.path) - 1:
            next_index = min(self.current_index + self.speed, len(self.path) - 1)
            next_pos = self.path[next_index]

            blocking_cars = get_blocking_cars(self.model.space,next_pos, self, test_agent)

            can_swap = False
            for other in blocking_cars:
                if other.current_index < len(other.path) - 1:
                    other_next_index = min(other.current_index + other.speed, len(other.path) - 1)
                    other_next_pos = other.path[other_next_index]
                    if tuple(other_next_pos) == tuple(self.geometry.coords[0]):
                        can_swap = True
                        break

            if not blocking_cars or can_swap:
                self.geometry = Point(next_pos)
                self.current_index = next_index
                self.travel_time += 1
                if self.current_index == len(self.path) - 1:
                    self.finished = True
                    print(f"Test agent reached destination in {self.travel_time} steps.")
            else:
                self.travel_time += 1  # Still count time even if blocked
        else:
            self.finished = True
                

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
        """Advance car agent one step"""

        if self.current_index < len(self.path) -1:
            next_index = min(self.current_index + self.speed, len(self.path) - 1)
            next_pos = self.path[next_index]

            # check cars at the next position
            blocking_cars = get_blocking_cars(self.model.space, next_pos, self, Car_agent)
            
            can_swap = False
            for other in blocking_cars:
                if other.current_index < len(other.path) - 1:
                    other_next_index = min(other.current_index + other.speed, len(other.path) - 1)
                    other_next_pos = other.path[other_next_index]
                    if tuple(other_next_pos) == tuple(self.geometry.coords[0]):
                        can_swap = True
                        break
            if not blocking_cars or can_swap:
                self.geometry = Point(next_pos)
                self.current_index = next_index
            else:
                print("blocked at", next_pos) # testing


        else:
            # Plan a new path to a random node
            start_node = self.nearest_node(self.geometry)
            end_node = random.choice(list(self.model.road_graph.nodes))
            self.plan_path(start_node, end_node)


def interpolate_linestring(line: LineString, spacing=5):
    """Helper function for points"""
    return [line.interpolate(distance) 
        for distance in range(0, int(line.length), spacing)] + [line.interpolate(line.length)]


class Main_model(mesa.Model):
    """Main model class for the neighborhood project"""

    def __init__(self, num_of_cars=100, speed_limit=40):
        super().__init__()
        
        self.start_time = datetime.now()
        self.sim_time = timedelta(seconds=0)
        self.space = mg.GeoSpace(warn_crs_conversion=False)
        self.running = True
        self.speed_limit = speed_limit

        # read in the geojson files
        road_path = "Roads.geojson"
        buildings_path = "Buildings.geojson"

        # Set up roads
        roads_comp = gpd.read_file(road_path).to_crs(epsg=3857)
        road_agents = [mg.GeoAgent(self, geometry=geom, crs=roads_comp.crs) for geom in roads_comp.geometry]
        self.space.add_agents(road_agents)

        # Set up buildings
        buildings_comp = gpd.read_file(buildings_path).to_crs(epsg=3857)
        buildings_agents = [mg.GeoAgent(self, geometry=geom, crs=buildings_comp.crs) for geom in buildings_comp.geometry]
        self.space.add_agents(buildings_agents)
        
        # Create a road graph from the roads
        self.road_graph = nx.Graph()
        spacing = 5  # Increased spacing to 50 meters between points
        for i, row in roads_comp.iterrows():
            line = row.geometry
            points = interpolate_linestring(line, spacing)
            #coords = list(row.geometry.coords)
            for start, end in zip(points[:-1], points[1:]):
                start_xy = (start.x, start.y)
                end_xy = (end.x, end.y)
                self.road_graph.add_edge(
                    start_xy, end_xy, weight=Point(start_xy).distance(Point(end_xy))
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

        
        northmost = max(nodes, key=lambda n: n[1])
        #southmost = min(nodes, key=lambda n: n[1])


        test_ac = mg.AgentCreator(test_agent, model=self, crs="EPSG:3857")
        test_car = test_ac.create_agent(
            geometry=Point(northmost),
        )
        test_car.speed = 2  # Speed for 40km/h = 11.11m/s ≈ 2.22 nodes (rounded to 2 nodes per step since nodes are 5m apart)
        self.space.add_agents([test_car])

        # debug
        #print("roads_comp.crs:", roads_comp.crs)
        #print("Point(start_node):", Point(start_node))

    def step(self):
        """Run one step of the model"""
        self.sim_time += timedelta(seconds=1)
        
        for agent in self.space.agents:
            agent.step()