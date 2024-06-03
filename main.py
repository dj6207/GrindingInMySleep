import threading
import time
import cv2 as cv
import pyautogui as pya
import numpy as np
import os 
import logging
import sys
from script_parser import StateGraph, generate_graph, NodeTypes, NodeClasses
from tkinter import filedialog
from typing import List, TypedDict, Union, Tuple, Dict
from PIL import Image 
from mouse import wind_mouse
from action_scripts import ACTION_DICT

logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s][%(levelname)s] %(message)s')

class ClickNodeResult(TypedDict):
    id: int
    type: NodeTypes
    priority: int 
    image: str
    shape: Tuple[int, int]
    coordinates: cv.typing.Point

class ActionNodeResult(TypedDict):
    id: int 
    type: NodeTypes
    priority: int 
    action: str

class EndNodeResult(TypedDict):
    id: int
    type: NodeTypes
    priority: int 

NodeResultTypes = Union[ClickNodeResult, ActionNodeResult, EndNodeResult]

class GrindInMySleep:
    def __init__(self, confidence:float=0.8) -> None:
        self.template_method:int = cv.TM_CCOEFF_NORMED
        self.confidence:float = confidence
        self.script_path:str = ""
        self.current_id:int = 0
        self.command_threads_list:List[threading.Thread] = []
        self.node_evaluation_results:List[NodeResultTypes] = []
        self.lock:threading.Lock = threading.Lock()
        self.node_visit:Dict[int, int] = {}

    def determine_path(self, id:int) -> None:
        data:NodeClasses = self.state_graph.get_metadata(id)
        logging.debug(f"Evaluating path {data.get('id')}")
        data_type:str = data.get('type')
        delay_time = data.get('delay')
        wait_time = data.get('wait')
        if delay_time:
            time.sleep(delay_time)
        if data_type == NodeTypes.Start.value:
            pass
        elif data_type == NodeTypes.End.value:
            with self.lock:
                end_node_result:EndNodeResult = {
                    "id": id,
                    "type": data.get('type'),
                    "priority": data.get('priority')
                }
                self.node_evaluation_results.append(end_node_result)
        elif data_type == NodeTypes.Action.value:
            with self.lock:
                action_node_result:ActionNodeResult = {
                    "id": id,
                    "type": data.get('type'),
                    "priority": data.get('priority'),
                    "action": data.get('action')
                }
                self.node_evaluation_results.append(action_node_result)
        else:
            templates:List[str] = data.get('images')
            with self.lock:
                match_results = self.find_match(templates=templates)
                # i, match_coordinates = self.find_match(templates=templates)
                if match_results is not None:
                    i, match_coordinates, match_height, match_width = match_results
                    click_node_result:ClickNodeResult = {
                        "id": id,
                        "type": data.get('type'),
                        "priority": data.get('priority'),
                        "coordinates": match_coordinates,
                        "image": data.get('images')[i],
                        "shape": (match_height, match_width)
                    }
                    self.node_evaluation_results.append(click_node_result)
        if wait_time:
            time.sleep(wait_time)
        
    def find_match(self, templates:List[str]) -> Tuple[int, cv.typing.Point, int, int] | None:
        capture: np.ndarray = self.get_screen_capture()
        for i, template in enumerate(templates):
            # TODO fix template finding in folders
            logging.debug(f"Finding match for {template}")
            template_image_path = os.path.join(os.getcwd(), 'assets', template + '.jpg')
            template_image = cv.imread(template_image_path)
            template_height, template_width, _ = template_image.shape
            result:np.ndarray = cv.matchTemplate(capture, template_image, self.template_method)
            _, max_val, _, max_loc = cv.minMaxLoc(result)
            if max_val > self.confidence:
                logging.debug(f"Match found for {template}")
                return i, max_loc, template_height, template_width
        return None

    def get_screen_capture(self) -> np.ndarray:
        logging.debug("Generating screen capture")
        capture: Image = pya.screenshot()
        # convert to opencv format
        capture_np: np.ndarray = np.array(capture)
        capture_cv: np.ndarray = cv.cvtColor(capture_np, cv.COLOR_RGB2BGR)
        logging.debug("Screen capture generated")
        return capture_cv
    
    def move_to(self, dest_x:float, dest_y:float, shape:Tuple[int, int]) -> None:
        height, width = shape
        dest_x_rand = np.random.randint(dest_x, dest_x+width)
        dest_y_rand = np.random.randint(dest_y, dest_y+height)
        current_x, current_y = pya.position()
        logging.debug(f"Moving from {(current_x, current_y)} to {(dest_x_rand, dest_y_rand)}")
        wind_mouse(
            start_x=current_x, 
            start_y=current_y, 
            dest_x=dest_x_rand, 
            dest_y=dest_y_rand, 
            move_mouse=lambda x,y: pya.moveTo(x=x, y=y), 
            G_0=9, 
            W_0=5, 
            M_0=25, 
            D_0=18
        )
        pya.mouseDown(duration=np.random.uniform(low=0.05, high=0.2))
        pya.mouseUp()

    def execute_action(self, action:str) -> None:
        action_function = ACTION_DICT.get(action)
        logging.debug(f"Executing Action {action_function}")
        if action_function:
            action_function()

    def execute_node(self, selected_result_node:NodeResultTypes, current_node:NodeClasses) -> None:
        node_type:str = selected_result_node.get('type')
        wait_time:float = current_node.get('wait')
        if node_type == NodeTypes.End.value:
            pass
        elif node_type == NodeTypes.Action.value:
            # do action
            action:str = selected_result_node.get('action')
            self.execute_action(action=action)
        else:
            coordinates = selected_result_node.get('coordinates')
            shape = selected_result_node.get('shape')
            if coordinates:
                self.move_to(dest_x=coordinates[0], dest_y=coordinates[1], shape=shape)
        if wait_time:
            time.sleep(wait_time)

    def start_grind(self) -> None:
        try:
            self.script_path:str = filedialog.askopenfilename()
            self.state_graph:StateGraph = generate_graph(file_path=self.script_path)
            current_node:NodeClasses = self.state_graph.get_metadata(self.current_id)
            
            while current_node.get('type') != NodeTypes.End.value:
                logging.debug(f"Current node {self.current_id}")
                self.node_evaluation_results = []
                neighbors:List[int] = self.state_graph.get_neighbors(self.current_id)
                logging.debug(f"Evaluating all paths for node {self.current_id}")
                for neighbor_id in neighbors:
                    command_thread = threading.Thread(target=self.determine_path, args=(neighbor_id,))
                    self.command_threads_list.append(command_thread)
                    command_thread.start()

                for command_thread in self.command_threads_list:
                    command_thread.join()
                
                # 
                logging.debug(f"Path evaluation complete for node {self.current_id}")
                sorted_results = sorted(self.node_evaluation_results, key=lambda x: x['priority'])
                if not len(sorted_results):
                    logging.error(f"No matches found at node {self.current_id}")
                    sys.exit()
                
                selected_node:NodeResultTypes = sorted_results[0]
                self.current_id = selected_node.get('id')
                current_node:NodeClasses = self.state_graph.get_metadata(self.current_id)
                self.execute_node(selected_result_node=selected_node, current_node=current_node)

                if self.node_visit.get(self.current_id) is not None:
                    self.node_visit[self.current_id] += 1
                else:
                    self.node_visit[self.current_id] = 1

                if self.node_visit.get(self.current_id) > 5:
                    logging.error(f"Possible infinite loop")
                    sys.exit()

                logging.debug(f"Moving to node {self.current_id}")
            logging.info(f"Finish executing {self.script_path}")
        except FileNotFoundError as fnf_err:
            sys.exit(fnf_err)

if __name__ == "__main__":
    grind = GrindInMySleep()
    grind.start_grind()