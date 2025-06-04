import geopandas as gpd
import networkx as nx
import mesa
import random
import mesa_geo as mg
from mesa_geo import AgentCreator
from shapely.geometry import LineString, Point




class Car_agent(mg.GeoAgent):
    """Car agent."""

    def __init__(self, model, geometry, crs,):
        """Create a new car agent."""

        super().__init__(model, geometry, crs)
        self.path = []  # List of points
        self.current_index = 0


        start_node = self.nearest_node(self.geometry)
        end_node = random.choice(list(self.model.road_graph.nodes))
        self.plan_path(start_node, end_node)

    def plan_path(self, start, end):
        try:
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
        nodes = list(self.model.road_graph.nodes)
        return min(nodes, key=lambda n: point.distance(Point(n)))

    def step(self):
        """Advance agent one step."""
        if self.current_index < len(self.path):
            next_pos = self.path[self.current_index]
            self.geometry = Point(next_pos)
            self.current_index += 1
        else:
            # Plan a new path to a random node
            start_node = self.nearest_node(self.geometry)
            end_node = random.choice(list(self.model.road_graph.nodes))
            self.plan_path(start_node, end_node)



class Road_agent(mg.GeoAgent):
    """Schelling segregation agent."""

    def __init__(self, model, geometry, crs):
        """Create a new Schelling agent.

        Args:
            agent_type: Indicator for the agent's type (minority=1, majority=0)
        """
        super().__init__(model, geometry, crs)


    def step(self):
        """Advance agent one step."""

    def __repr__(self):
        return "Agent " + str(self.unique_id)




class Main_model(mesa.Model):
    """Model class for the Schelling segregation model."""

    def __init__(self, num_of_cars=100, speed_limit=40):
        super().__init__()

        self.space = mg.GeoSpace(warn_crs_conversion=False)
        self.running = True

        # read in the geojson files
        ac = mg.AgentCreator(Road_agent, model=self)
        road_path = "Roads.geojson"
        buildings_path = "Buildings.geojson"

        # Set up roads
        roads_comp = gpd.read_file(road_path)
        road_agents = ac.from_GeoDataFrame(roads_comp)
        self.space.add_agents(road_agents)

        # Set up buildings
        buildings_comp = gpd.read_file(buildings_path)
        buildings_agents = ac.from_GeoDataFrame(buildings_comp)
        self.space.add_agents(buildings_agents)
        
        self.road_graph = nx.Graph()
        for i, row in roads_comp.iterrows():
            coords = list(row.geometry.coords)
            for start, end in zip(coords[:-1], coords[1:]):
                self.road_graph.add_edge(
                    start, end, weight=Point(start).distance(Point(end))
                )

        # Set up cars
        car_ac = mg.AgentCreator(Car_agent, model=self,crs=roads_comp.crs)
        car_agents = []
        for i in range(num_of_cars):
            # Create car agents with random positions 
            start_node = random.choice(list(self.road_graph.nodes))
            car_agent = car_ac.create_agent(
                geometry=Point(start_node),
            )
            car_agents.append(car_agent)
        self.space.add_agents(car_agents)

        


    def step(self):
        """Run one step of the model."""
        for agent in self.space.agents:
                agent.step()