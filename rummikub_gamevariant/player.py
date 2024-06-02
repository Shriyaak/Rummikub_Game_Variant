from util import compare_func

class Player:

    def __init__(self,rack,auto_play=False):
        self.rack=[]
        self.auto_play = False
        self.status = 0
        self.rack = sorted(rack,key=compare_func)
        self.score = 0
    
    def update_rack(self,rack):
        self.rack = sorted(rack,key=compare_func)
    
    def add_tile(self,tile):
        self.rack.append(tile)
        self.rack = sorted(self.rack,key=compare_func)
    
    def get_tiles_value(self):
        value = 0
        for tile in self.rack:
            value = value + tile[1]
        return value
    def reset(self,rack=[]):
        self.auto_play = False
        self.status = 0
        self.score = 0
