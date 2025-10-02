## ABM Neighborhood Model

# Abstract
This paper presents an Agent-Based Model (ABM) traffic simulation designed to evaluate how urban development and demand affect congestion on road networks. The model converts standard vector road data into a directed segment network and simulates vehicles moving along the true geometries at a consistent speed. Local capacity constraints produce emergent congestion and queues without hard-coding bottlenecks. Users can vary the number of vehicles to explore before/after scenarios and assess congestion.

The model is designed to be reproducible, it runs on user-supplied road networks (GeoJSON files) and produces interpretable metrics such as travel time. Emphasizing simplicity, it supports rapid screening of development proposals and network interventions before more detailed operational modeling. While intentionally simplified, the approach yields insights into where and why congestion forms and how results shift under alternative assumptions, helping quickly visualize what kind of impact new developments will have on the area.

# Introduction
Urban development projects can substantially reshape traffic demand and place new pressures on existing road infrastructure. Anticipating these effects before construction is critical for sustainable planning and informed decision-making. Traditional macroscopic traffic models effectively capture traffic flows but often obscure localized interactions that generate queues and delays along specific road segments.

Agent-based modeling (ABM) addresses this limitation by representing individual vehicles and their interactions within the network. This bottom-up perspective reveals emergent congestion patterns that are difficult to capture in large models and provides a method of evaluating the impacts of proposed developments.

Building on these strengths, the model operates on user-provided road networks. Standard street centerlines are transformed into a directed segment graph, and vehicles are simulated along their true geometries under a consistent speed parameter. Because interactions are constrained by local segment capacities, queues and congestion emerge. This design enables rapid and reproducible before-and-after comparisons of development proposals and network interventions across diverse urban contexts.

# Data
The model currently uses a GeoJSON file containing road network data for the Waterloo area. This dataset is publicly available through the City of Waterloo Open Data portal. Once imported the raw vector data is transformed into a directed network of road segments. Each road is subdivided into small, navigable components that the car agents will traverse over. 
This segmentation process is essential because it restructures the data into a form compatible with agent behavior, enabling the emergence of congestion and flow dynamics from the current infrastructure. The framework is not limited to Waterloo. Any valid GeoJSON file can be imported, allowing the model to be adapted for different cities or regions and supporting localized studies of traffic flow and congestion. 
Agents
Two agent types are implemented in the simulation: car agents and a testing agent, each serving distinct roles in representing and evaluating traffic dynamics. 

Car agents represent the general population of vehicles traveling within the network. Their behavior is designed to mimic the random behavior of real-world travel patterns. At initialization, each car agent is assigned an origin and destination, chosen randomly from the available network of buildings. Using Dijkstra's algorithm, the agent identifies the shortest path between the two points and then traverses that route at a constant speed. 

Upon reaching their destination the car agents select a new destination and repeat the process, continuously generating traffic throughout the simulation. This cyclical behavior allows the model to approximate background traffic flow over time, capturing how vehicles interact and contribute to the local traffic. 

The testing agent is designed as a controlled probe within the system. It follows a fixed and repeatable route between two predefined points in the network. Its role is to act as a performance benchmark, allowing for measurement of travel times under different conditions. 

Because the testing agent’s behavior does not vary, changes in its measured travel time directly reflect the influence of external factors such as the increase in traffic demand and the introduction of new developments. In this way, the testing agent provides a consistent basis for evaluating the impacts of proposed changes.

# Visualization
The simulation incorporates an interactive front-end built with Solara, which provides a simple yet effective interface for controlling and observing the model in real time. The visualization displays the road network and the movement of agents across its segments, allowing users to directly observe congestion formation and traffic dynamics as the simulation unfolds. 

A small set of controls enables users to manage the simulation process:
Start: Starts continuously stepping forward at a constant rate
Pause: Pauses the simulation at its current step
Step: Advances the simulation forward by one step

This allows users to run the scenario and also visually examine how demand changes and traffic congestion emerge within the network. By combining the travel time of the test agent and the real-time visual inspection, we can connect the results and make informed development decisions.

# Resources
The Model integrates several of Python's libraries that support data processing, simulation, and visualization. GeoPandas is used to import and manipulate GeoJSON road network data. NetworkX provides graph-based algorithms, including Dijkstra's and also takes care of the segmentation of the road network. Mesa is the foundation of the simulation, managing agent scheduling and core logic, while Mesa-Geo expands the framework further to spatially explicit agents and road geometries. Finally, Solara provides the front-end interface, allowing for the interactive visualization and simulation controls. 

# Conclusion
This paper presents an agent-based model for simulating traffic congestion under conditions of urban development and changing demand. By transforming GeoJSON road data into a directed segment network and populating it with car agents and a testing agent, the system captures congestion patterns and provides interpretable performance metrics. The framework emphasizes reproducibility and makes it well-suited for preliminary evaluations of development proposals. 
