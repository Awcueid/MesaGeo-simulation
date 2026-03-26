import geopandas as gpd
import networkx as nx
import mesa
from mesa.datacollection import DataCollector
import random
import mesa_geo as mg
from shapely.geometry import LineString, Point
from datetime import datetime, timedelta
from bicycle_agent import Bicycle_agent, test_bicycle
from pedestrian_agent import Pedestrian_agent, test_pedestrian


def interpolate_linestring(line: LineString, spacing=5):
    """Helper function for points"""
    return [line.interpolate(distance)
        for distance in range(0, int(line.length), spacing)] + [line.interpolate(line.length)]


def connect_components(graph):
    """Connect disconnected components in the road graph."""
    components = list(nx.weakly_connected_components(graph))
    if len(components) <= 1:
        return

    components = sorted(components, key=len, reverse=True)
    largest_component = components[0]

    for component in components[1:]:
        min_distance = float("inf")
        closest_pair = None

        for node1 in largest_component:
            for node2 in component:
                distance = Point(node1).distance(Point(node2))
                if distance < min_distance:
                    min_distance = distance
                    closest_pair = (node1, node2)

        if closest_pair:
            node1, node2 = closest_pair
            graph.add_edge(node1, node2, weight=min_distance, lane=0, direction=1)
            graph.add_edge(node2, node1, weight=min_distance, lane=0, direction=-1)
    print("All components connected.")
    
class Trading_model(mesa.Model):
    """Trading simulation model with only bicycles and pedestrians."""

    def __init__(self, num_of_bicycles=50, num_of_pedestrians=100):
        super().__init__()

        self.start_time = datetime.now()
        self.sim_time = timedelta(seconds=0)
        self.space = mg.GeoSpace(warn_crs_conversion=False)
        self.running = True
        self.road_lanes = 1
        self.bicycle_lane_occupancy: dict[tuple, object] = {}

        # Read in the geojson files
        road_path = "Maps/Roads.geojson"
        buildings_path = "Maps/Buildings.geojson"

        # Set up roads
        roads_comp = gpd.read_file(road_path).to_crs(epsg=3857)
        road_agents = [mg.GeoAgent(self, geometry=geom, crs=roads_comp.crs) for geom in roads_comp.geometry]
        self.space.add_agents(road_agents)

        # Set up buildings
        buildings_comp = gpd.read_file(buildings_path).to_crs(epsg=3857)
        buildings_agents = []
        for _, row in buildings_comp.iterrows():
            agent = mg.GeoAgent(self, geometry=row.geometry, crs=buildings_comp.crs)
            agent.OBJECTID = row["OBJECTID"]
            buildings_agents.append(agent)
        self.space.add_agents(buildings_agents)

        # Create a road graph from the roads
        self.road_graph = nx.MultiDiGraph()
        spacing = 5
        max_lanes_seen = 1
        for i, row in roads_comp.iterrows():
            line = row.geometry
            points = interpolate_linestring(line, spacing)

            raw_lanes = row.get("NUMBER_LANES", None)
            seg_lanes = int(raw_lanes) if (raw_lanes and not gpd.pd.isna(raw_lanes) and int(raw_lanes) > 0) else 1
            max_lanes_seen = max(max_lanes_seen, seg_lanes)

            flow = str(row.get("FLOW_DIRECTION", "TwoWay")).strip()
            two_way = (flow != "FromTo")

            raw_speed = row.get("SPEED_ZONE", 40.0)
            speed_kmh = float(raw_speed) if (raw_speed and not gpd.pd.isna(raw_speed) and float(raw_speed) > 0) else 40.0

            for start, end in zip(points[:-1], points[1:]):
                start_xy = (start.x, start.y)
                end_xy = (end.x, end.y)
                dist = Point(start_xy).distance(Point(end_xy))
                for lane in range(seg_lanes):
                    self.road_graph.add_edge(
                        start_xy, end_xy,
                        key=lane, weight=dist, lane=lane,
                        num_lanes=seg_lanes, speed_kmh=speed_kmh, direction=1,
                    )
                    if two_way:
                        self.road_graph.add_edge(
                            end_xy, start_xy,
                            key=lane, weight=dist, lane=lane,
                            num_lanes=seg_lanes, speed_kmh=speed_kmh, direction=-1,
                        )

        self.road_lanes = max_lanes_seen
        connect_components(self.road_graph)

        nodes = list(self.road_graph.nodes)

        # Set up bicycles
        bicycle_ac = mg.AgentCreator(Bicycle_agent, model=self, crs="EPSG:3857")
        bicycle_agents = []
        for i in range(num_of_bicycles):
            start_node = random.choice(nodes)
            bicycle_agent = bicycle_ac.create_agent(geometry=Point(start_node))
            bicycle_agent.speed = 1
            bicycle_agents.append(bicycle_agent)
        self.space.add_agents(bicycle_agents)

        # Set up pedestrians
        pedestrian_ac = mg.AgentCreator(Pedestrian_agent, model=self, crs="EPSG:3857")
        pedestrian_agents = []
        for i in range(num_of_pedestrians):
            start_node = random.choice(nodes)
            pedestrian_agent = pedestrian_ac.create_agent(geometry=Point(start_node))
            pedestrian_agent.speed = 1
            pedestrian_agents.append(pedestrian_agent)
        self.space.add_agents(pedestrian_agents)

        # Collect all stepping agents
        self.agents_list = [
            agent for agent in self.space.agents if callable(getattr(agent, "step", None))
        ]

    def step(self):
        """Run one step of the model"""
        self.sim_time += timedelta(seconds=1)

        for agent in self.agents_list:
            agent.step()

        if hasattr(self, "datacollector"):
            self.datacollector.collect(self)