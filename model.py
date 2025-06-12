import geopandas as gpd
import networkx as nx
import mesa
import random
import mesa_geo as mg
from mesa_geo import AgentCreator
from shapely.geometry import LineString, Point



class Car_agent(mg.GeoAgent):

    def __init__(self, model, geometry, crs, speed=1):
        """Create a new car agent"""

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
        """Advance agent one step"""

        if self.current_index < len(self.path) -1:
            next_index = min(self.current_index + self.speed, len(self.path) - 1)
            next_pos = self.path[next_index]
            self.geometry = Point(next_pos)
            self.current_index = next_index
        else:
            # Plan a new path to a random node
            start_node = self.nearest_node(self.geometry)
            end_node = random.choice(list(self.model.road_graph.nodes))
            self.plan_path(start_node, end_node)



class Road_agent(mg.GeoAgent): 

    def __init__(self, model, geometry, crs):
        """Create a new road agent."""
        super().__init__(model, geometry, crs)


    def step(self):
        """Advance agent one step."""

    def __repr__(self):
        return "Agent " + str(self.unique_id)


def interpolate_linestring(line: LineString, spacing=5):
    """Helper function for points"""
    return [line.interpolate(distance) 
        for distance in range(0, int(line.length), spacing)] + [line.interpolate(line.length)]


class Main_model(mesa.Model):
    """Main model class for the neighborhood project"""

    def __init__(self, num_of_cars=100, speed_limit=40):
        super().__init__()
        self.time = 0
        self.space = mg.GeoSpace(warn_crs_conversion=False)
        self.running = True

        # read in the geojson files
        ac = mg.AgentCreator(Road_agent, model=self)
        road_path = "Roads.geojson"
        buildings_path = "Buildings.geojson"

        # Set up roads
        roads_comp = gpd.read_file(road_path).to_crs(epsg=3857)
        road_agents = ac.from_GeoDataFrame(roads_comp)
        self.space.add_agents(road_agents)

        # Set up buildings
        buildings_comp = gpd.read_file(buildings_path).to_crs(epsg=3857)
        buildings_agents = ac.from_GeoDataFrame(buildings_comp)
        self.space.add_agents(buildings_agents)
        
        # Create a road graph from the roads
        self.road_graph = nx.Graph()
        spacing = 10 
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
        for i in range(num_of_cars):  
            # Create car agents with random positions 
            start_node = random.choice(list(self.road_graph.nodes))
            car_agent = car_ac.create_agent(
                geometry=Point(start_node),
            )
            car_agent.speed = speed_limit  # Set speed limit for the car
            car_agents.append(car_agent)
        self.space.add_agents(car_agents)


        # debug
        print("roads_comp.crs:", roads_comp.crs)
        print("start_node:", start_node)
        print("Point(start_node):", Point(start_node))

    def step(self):
        """Run one step of the model"""
        self.time += 5
        for agent in self.space.agents:
                agent.step()