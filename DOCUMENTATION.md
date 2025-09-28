# Traffic Simulation Model Documentation

## Overview
This is a traffic simulation model built using the Mesa agent-based modeling framework. The simulation models cars moving through a real road network loaded from GeoJSON data, with realistic traffic flow and congestion.

## Core Components

### 1. Road Network Infrastructure

#### RoadSegment Class
Think of a road segment as a single stretch of road between two intersections. If you imagine a city block, each side of the block would be a separate road segment.
Each segment has these properties:

- **Geometry**: The actual shape and path of the road segment
- **Length**: How long the segment is in meters
- **Current Occupants**: Which cars are currently driving on this segment
- **Start and End Points**: The intersections this segment connects

#### Road Network Creation
The model takes real geographic data (GeoJSON) and converts it into a network of road segments:

1. **Loading Geographic Data**: Reads actual street layouts from map data
2. **Creating Intersections**: Identifies where roads meet (street corners)
3. **Building Segments**: Creates individual road segments between each intersection
4. **Bidirectional Roads**: Most roads allow traffic in both directions, so each physical road becomes two segments (one for each direction)

### 2. Traffic Agents (Cars)

#### Car Agent Class
Each car in the simulation is an independent agent that makes its own decisions:

**Movement Behavior**:
- Cars move at a realistic speed (equivalent to about 40 km/h or 25 mph)
- They follow the actual geometry of roads, not just straight lines
- Each car moves 2 meters forward every simulation step

**Navigation**:
- Cars plan routes from their starting point to their destination
- They use the road network to find the shortest path
- When they reach intersections, they choose the next road segment based on their planned route

**Traffic Rules**:
- When blocked, cars wait at their current position until space opens up
- Cars respect the directional flow of traffic

#### Test Agent
There's a special red car that demonstrates the system:
- Always travels from the northernmost point to the southernmost point
- Helps visualize how the pathfinding and movement work
- Shows how cars navigate through the entire network

### 3. Traffic Management System

#### Capacity Management
- **Congestion Effects**: When segments fill up, traffic jams form
- **Dynamic Flow**: Cars must wait for space to open up before proceeding

#### Movement Coordination
The simulation ensures realistic traffic flow:
- **Speed Consistency**: All cars move at the same base speed
- **Segment-Based Movement**: Cars progress along entire road segments, not just point-to-point

### 4. Simulation Control

#### Main Model Class
This is the "brain" of the simulation that coordinates everything:

**Initialization**:
- Loads and processes the geographic road data
- Creates the network of road segments and intersections
- Spawns cars at random locations throughout the network
- Sets up the special test agent

**Step-by-Step Execution**:
- Each simulation step represents a small time interval (one second)
- All cars move simultaneously during each step
- The model tracks overall statistics and manages the simulation flow

#### Scheduler
Uses Mesa's built-in scheduler to manage when each car takes its turn:
- Ensures all cars move in an organized fashion
- Prevents conflicts between cars trying to move at the same time
- Maintains consistent timing across the simulation

### 5. User Interface

#### Web-Based Visualization
The simulation runs in a web browser showing:
- **Interactive Map**: Real road network with cars moving along streets
- **Real-Time Animation**: Cars moving smoothly through the network
- **Test car**: Red color for the test car

#### Control Parameters
Users can adjust the simulation through sliders:

**Number of Cars** (1-1000):
- Controls how many regular cars are in the simulation
- More cars create more traffic and congestion
- Fewer cars show individual movement patterns more clearly

### 6. Data Flow

#### How Everything Works Together

1. **Startup**: 
   - Load real street map data
   - Convert streets into a network of road segments
   - Create cars and place them randomly on the network

2. **Each Simulation Step**:
   - Every car calculates where it wants to move next
   - Cars check if the next road segment has available space
   - If space is available, cars move forward along their route
   - If space is not available, cars wait (creating traffic)

3. **Continuous Operation**:
   - The simulation runs continuously, step by step
   - Cars complete their journeys and new ones can be added
   - Traffic patterns emerge naturally from individual car behaviors

## Technical Implementation Details

### File Structure
- **model.py**: Contains all the core simulation logic
- **app.py**: Web interface and visualization controls
- **visualize.py**: Network visualization tools
- **Roads.geojson**: Geographic data for road network
- **Buildings.geojson**: Geographic data for buildings (visual context)

### Key Classes and Their Roles

#### RoadSegment
- Represents individual road sections
- Manages capacity and occupancy
- Tracks which cars are currently on the segment

#### Car_agent
- Individual car behavior and movement
- Route planning and navigation
- Traffic rule compliance

#### test_agent
- Demonstration agent for system testing
- Shows complete network traversal
- Helps validate pathfinding algorithms

#### Main_model
- Central coordination of all components
- Network initialization and management
- Simulation stepping and timing