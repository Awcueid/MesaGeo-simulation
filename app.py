import solara
from mesa.visualization import Slider, SolaraViz # add make_plot_component
from mesa_geo.visualization import make_geospace_component
from model import Main_model

model_params = {
    # sliders for model parameters
    "num_of_cars": Slider("Number of Cars", 100, 1, 1000, 10),
    "speed_limit": Slider("Speed Limit", 40, 1, 100, 1),
}



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
    elif agent.geometry.geom_type == "Point":
        print("Drawing point agent",agent.geometry)
        portrayal = {  # set cars to purple
            "type": "point",  
            "color": "purple", 
            "radius": 5,  # check why size doesent work
        }
    return portrayal


model = Main_model()

# create the solara page
page = SolaraViz(
    model,
    [
        make_geospace_component(Main_draw, zoom=14, height="100vh", width="100vw"),
    ],
    model_params=model_params,
    name="Neighborhood Project",

)

page  # noqa