import pyautogui as pya
import numpy as np
import time
from typing import Dict, Callable
from mouse import wind_mouse

FunctionType = Callable[..., any]

def scroll_down() -> None:
    screen_width, screen_height = pya.size()
    screen_half = screen_width//2
    screen_one_fourths = screen_height//3
    screen_three_fourths = (screen_height*3)//4

    tolerance_x:int = screen_width//38
    tolerance_y:int = screen_height//38

    start_x = screen_half + np.random.randint(-tolerance_x, tolerance_x)
    start_y = screen_three_fourths + np.random.randint(-tolerance_y, tolerance_y)
    end_x = screen_half + np.random.randint(-tolerance_x, tolerance_x)
    end_y = screen_one_fourths + np.random.randint(-tolerance_y, tolerance_y)
    pya.moveTo(x=start_x, y=start_y)
    pya.mouseDown()
    wind_mouse(
        start_x=start_x, 
        start_y=start_y, 
        dest_x=end_x, 
        dest_y=end_y, 
        move_mouse=lambda x,y: pya.moveTo(x=x, y=y), 
        G_0=9, 
        W_0=3, 
        M_0=30, 
        D_0=25
    )
    pya.mouseUp()

ACTION_DICT:Dict[str, FunctionType] = {
    "scroll_down": scroll_down,
}

if __name__ == "__main__":
    scroll_down()