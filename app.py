import solara
from mesa.visualization import Slider, SolaraViz # add make_plot_component
from mesa_geo.visualization import make_geospace_component
from model import Main_model, test_agent

model_params = {
    # sliders for model parameters
    "num_of_cars": Slider("Number of Cars", 100, 1, 1000, 1),
}

def Time(model):
    """Display formatted simulation time"""
    try:
        hours = int(model.sim_time.total_seconds() // 3600)
        minutes = int((model.sim_time.total_seconds() % 3600) // 60)
        seconds = int(model.sim_time.total_seconds() % 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return solara.Text(f"Simulation time: {time_str}")
    except AttributeError:
        return solara.Text("Time not available")

def Main_draw(agent): 
    """Portrayal Method for canvas"""
    
    if agent.geometry.geom_type == "Polygon":
        area = agent.geometry.area  
        if area > 43677.19: # change this to use id later
            portrayal = { # set new high rise building to red
                "type": "polygon",  
                "color": "red",  
            }
        else:
            portrayal = {  # set rest of houses to green
                "type": "polygon",  
                "color": "green",  
            }
    elif agent.geometry.geom_type == "LineString":
        portrayal = {  # set roads to blue
            "type": "linestring",  
            "color": "blue",  
        }
    elif isinstance(agent, test_agent):
        print("Drawing special agent")
        portrayal = {
            "type": "point",  
            "color": "red",  # set special agent to red
            "radius": 5,
        }
    elif agent.geometry.geom_type == "Point":
        print("Drawing point agent",agent.geometry)
        portrayal = {  # set cars to purple
            "type": "point",  
            "color": "purple", 
            "radius": 5,  # check why size doesent work
        }
    return portrayal

# run the model
model = Main_model()

# create the solara page
page = solara.Column(
    [
        SolaraViz(
            model,
            [
                make_geospace_component(Main_draw, zoom=14, height="100vh", width="100vw"),
            ],
            model_params=model_params,
            name="Neighborhood Project",
        ),Time(model)
    ]
)
page  # noqa