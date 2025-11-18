import geopandas as gpd
import networkx as nx
import mesa
import random
import mesa_geo as mg
from shapely.geometry import LineString, Point
from datetime import datetime, timedelta
from car_agent import Car_agent, test_car
from bicycle_agent import Bicycle_agent
from pedestrian_agent import Pedestrian_agent

def interpolate_linestring(line: LineString, spacing=5):
    """Helper function for points"""
    return [line.interpolate(distance) 
        for distance in range(0, int(line.length), spacing)] + [line.interpolate(line.length)]


def connect_components(graph):
    """Connect disconnected components in the road graph."""

    # Find weakly connected components
    components = list(nx.weakly_connected_components(graph))
    if len(components) <= 1:
        print("The road graph is already connected.")
        return

    print(f"Connecting {len(components)} weakly connected components...")

    # Sort components by size (largest first)
    components = sorted(components, key=len, reverse=True)
    largest_component = components[0]

    # Connect smaller components to the largest component
    for component in components[1:]:
        min_distance = float("inf")
        closest_pair = None

        # Find the closest pair of nodes between the largest component and the current component
        for node1 in largest_component:
            for node2 in component:
                distance = Point(node1).distance(Point(node2))
                if distance < min_distance:
                    min_distance = distance
                    closest_pair = (node1, node2)

        # Add an edge to connect the components
        if closest_pair:
            node1, node2 = closest_pair
            graph.add_edge(node1, node2, weight=min_distance, lane=0, direction=1)
            graph.add_edge(node2, node1, weight=min_distance, lane=0, direction=-1)
            print(f"Connected {node1} to {node2} with distance {min_distance:.2f}.")

    print("All components connected.")


class Main_model(mesa.Model):
    """Main model class for the neighborhood project"""

    def __init__(self, num_of_cars=100, speed_limit=40, road_lanes=1, fix_graph=True, num_of_bicycles=50, num_of_pedestrians=100):
        super().__init__()
        
        self.start_time = datetime.now()
        self.sim_time = timedelta(seconds=0)
        self.space = mg.GeoSpace(warn_crs_conversion=False)
        self.running = True
        self.speed_limit = speed_limit
        self.road_lanes = road_lanes
        # Separate occupancies so cars and bicycles use different lanes
        self.car_lane_occupancy: dict[tuple, object] = {}
        self.bicycle_lane_occupancy: dict[tuple, object] = {}

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
        # optimize / fix the graph if needed
        connect_components(self.road_graph)

        
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
            # Cars: ~40 km/h -> ~2 nodes/step (5 m spacing)
            car_agent.speed = 2
            car_agents.append(car_agent)
        self.space.add_agents(car_agents)

        # Set up bicycles
        bicycle_ac = mg.AgentCreator(Bicycle_agent, model=self, crs="EPSG:3857")
        bicycle_agents = []
        for i in range(num_of_bicycles):
            start_node = random.choice(nodes)
            bicycle_agent = bicycle_ac.create_agent(
                geometry=Point(start_node),
            )
            # Bicycles: ~15 km/h -> about half car speed
            bicycle_agent.speed = 1
            bicycle_agents.append(bicycle_agent)
        self.space.add_agents(bicycle_agents)

        # Set up pedestrians
        pedestrian_ac = mg.AgentCreator(Pedestrian_agent, model=self, crs="EPSG:3857")
        pedestrian_agents = []
        for i in range(num_of_pedestrians):
            start_node = random.choice(nodes)
            pedestrian_agent = pedestrian_ac.create_agent(
                geometry=Point(start_node),
            )
            # Pedestrians: move one node every 2 model steps
            pedestrian_agent.speed = 1
            pedestrian_agents.append(pedestrian_agent)
        self.space.add_agents(pedestrian_agents)

        # Track car and bicycle agents
        self.cars = [
            agent for agent in self.space.agents if callable(getattr(agent, "step", None))
        ]
        
        northmost = max(nodes, key=lambda n: n[1])
        #southmost = min(nodes, key=lambda n: n[1])


        test_ac = mg.AgentCreator(test_car, model=self, crs="EPSG:3857")
        test_car_agent = test_ac.create_agent(
            geometry=Point(northmost),
        )
        test_car_agent.speed = 2  # Speed for 40km/h = 11.11m/s ≈ 2.22 nodes (rounded to 2 nodes per step since nodes are 5m apart)

        # add the test car to the space and cars list
        self.space.add_agents([test_car_agent])
        self.cars.append(test_car_agent)

        # debug
        #print("roads_comp.crs:", roads_comp.crs)
        #print("Point(start_node):", Point(start_node))

    def step(self):
        """Run one step of the model"""
        self.sim_time += timedelta(seconds=1)
        
        for agent in self.cars:
            agent.step()