import json
import sys
from typing import Any, Dict, TypedDict, List, Union
from enum import Enum
from tkinter import filedialog

# Node types that does different things
# Start node indicates the start of the graph
# End node indicates the end of the graph
# Action node performs a mouse action like swiping up
# Click node search for image and click

# Json 
# id: unique identifier of the node
# type: identifies the node type
# links: other nodes that it connects to


class NodeTypes(Enum):
    Start = "S"
    End = "E"
    Action = "A"
    Click = "C"

class ClickNode(TypedDict):
    id: int
    type: str
    comments: str
    priority: int
    images: List[str]
    delay: float
    wait: float
    clicks: int
    links: List[int]

class ActionNode(TypedDict):
    id: int
    type: str 
    comments: str 
    priority: int 
    action: str
    delay: float 
    wait: float
    links: List[int]

class StartNode(TypedDict):
    id: int
    type: str
    comments: str
    links: List[int]

class EndNode(TypedDict):
    id: int
    type: str
    comments: str
    priority: int

NodeClasses = Union[ClickNode, ActionNode, EndNode, StartNode]

class Script(TypedDict):
    script:str
    comments:str
    nodes:List[NodeClasses]

class StateGraph:
    def __init__(self) -> None:
        self.graph:Dict[int, List[int]] = {}
        self.node_data:Dict[int, NodeClasses] = {}
    
    def add_node(self, node_id:int, data:NodeClasses) -> None:
        if node_id not in self.node_data:
            self.node_data[node_id] = data
            self.graph[node_id] = []
        else:
            sys.exit("Node with same id")
        
    def add_edge(self, node_id:int, edges:List[int]) -> None:
        if self.graph.get(node_id) is not None:
            self.graph[node_id] = edges
        else:
            sys.exit("Node does not exist")
        
    def get_neighbors(self, id:int) -> List[int]:
        if id in self.graph:
            return self.graph[id]
        else:
            sys.exit("Node not found in graph")

    def get_metadata(self, id:int) -> NodeClasses:
        if id in self.node_data:
            return self.node_data[id]
        else:
            sys.exit("Node not found in graph")
        
    def print_graph(self):
        print(self.graph)

    def print_node_data(self):
        print(self.node_data)


def generate_graph(file_path:str) -> StateGraph:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data:Script = json.load(file)
            nodes:List[NodeClasses] = data.get('nodes')
            new_graph = StateGraph()
            for node in nodes:
                node_id = node.get('id')
                new_graph.add_node(node_id=node_id, data=node)
                new_graph.add_edge(node_id=node_id, edges=node.get('links'))
            return new_graph
    except FileNotFoundError as fnf_err:
        sys.exit(fnf_err)
    except json.JSONDecodeError as json_err:
        sys.exit(json_err)

if __name__ == "__main__":
    script_path = filedialog.askopenfilename()
    graph:StateGraph = generate_graph(file_path=script_path)
    graph.print_graph()
    graph.print_node_data()
    