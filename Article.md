## ABM Neighborhood Model
# Abstract
An Agent-Based Model (ABM) traffic simulation that evaluates how urban development and demand changes affect congestion on road networks. The model converts standard vector road data into a directed segment network and simulates vehicles moving along the true geometries at a consistent speed. Local capacity constraints produce emergent congestion and queues without hard-coding bottlenecks. Users can vary demand and segment capacities to explore before/after scenarios and assess congestion.

The framework is designed to be portable and reproducible: it runs on user-supplied road networks (GeoJSON) and produces interpretable metrics, including travel time distributions. Emphasizing simplicity and transparency, it supports rapid screening of development proposals and network interventions before more detailed operational modeling. While intentionally simplified, the approach yields actionable insights into where and why congestion forms and how results shift under alternative assumptions, helping practitioners prioritize interventions and focus data collection on the most influential corridors.

# Introduction
Urban development projects can substantially shift travel demand and stress existing road infrastructure. Anticipating these impacts before construction is essential for sustainable planning. While traditional macroscopic traffic models capture aggregate flows well, they can obscure localized interactions that generate queues and delays on specific links.

Agent-based modeling (ABM) complements these approaches by simulating individual vehicles and their interactions within the road network. This bottom-up perspective helps reveal emergent patterns—such as bottleneck formation, spillback, and network-wide sensitivity to demand and capacity changes—that are difficult to infer from aggregate models alone.

This work introduces a generalizable, data-agnostic ABM that others can reuse with their own road networks. The pipeline converts user-supplied street centerlines into a directed, capacity-aware segment graph and simulates vehicles moving along the true geometries at a consistent speed. Local capacity constraints govern interactions, so congestion arises naturally rather than being hard-coded. The framework is designed for rapid, reproducible before/after comparisons of development proposals and network interventions.

Contributions (brief):
- A portable ABM pipeline that ingests standard vector road data and builds a directed, capacity-aware segment network.
- Scenario levers (vehicle volume, per-segment capacities, duration) and interpretable metrics (travel times, throughput, occupancy, delay indices) for comparable analyses.
- A lightweight, reproducible workflow with seeds, replications, and logging to support credible comparisons without heavy calibration.

Paper outline. We next describe the data requirements and preprocessing workflow, summarize the modeling approach, define scenario design and experimental setup, present evaluation metrics and validation checks, and conclude with results, implications, and limitations.

# Model Design

# Data
The system currently uses a GeoJSON file filled with data of a road network in the Waterloo area. This file can be found on the City of Waterloo Open Data which is open to the public. Utilizing this file we are able to generate the road system used by the simulations agents, and lay the foundations for the entire system.
