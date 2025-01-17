from set_generator import SetGenerator
from itertools import combinations
from collections import defaultdict
from console import Console
from util import *
import time

INITIAL_MELD_PLAY = 0
NORMAL_PLAY = 1
CHECK_PLAY = 2

class SolveTiles:
    begin_time = time.time()
    max_search_time = 20

    def __init__(self,sg):
        self.yellow = ['yellow_1', 'yellow_2']
        self.cyan = ['cyan_1', 'cyan_2']
        self.black = ['black_1', 'black_2']
        self.red = ['red_1', 'red_2']
        self.blue = ['blue_1', 'blue_2']
        #self.sg = SetGenerator()
        self.sg = sg
        self.con = Console()
        # self.begin_time = time.time()
        # self.max_search_time = 10

    def solve_tiles(self, board=[], rack=[]):
        '''This function appends board and rack to each other and then calls solution_finder on the union'''
        SolveTiles.begin_time = time.time()
        union=[]
        for set in board:
            for tile in set:
                union.append(tile)
        union += rack
        solutions = self.solution_finder(1, [], union)
        return solutions

    def solution_finder(self, n=1, solutions=[], tiles=[]):
        '''This solution finder recursively finds every combination of tiles. It starts at n=1 which stands for tile value
            So first all tiles with value 1 are evaluated. at n=1, we start new runs and make new groups, and then make
            this function calls itsself with n+1 and all found solutions so far.
            At n=2, for example, we again find new runs and new groups, but we also try to find new groups/runs in existing solutions.
             We also try to extend runs in previous solutions. All these new solutions/options are saved and recursed on.'''
        print(n)
        newsolutions = []
        if n > 1:
            newsolutions.extend(solutions)
        if time.time()-SolveTiles.begin_time>SolveTiles.max_search_time:
            return newsolutions

        # here we call find_new_groups to find all the new possible groups at the current n value
        new_groups = self.find_new_groups(n, tiles)

        if len(new_groups) != 0:  # if new groups are found
            newsolutions.extend(new_groups)  # add all the new possible groups as a new solution to newsolutions

        # call start_new_runs to find all the new single tile solutions
        new_run_starts = self.start_new_runs(tiles, n)

        if len(new_run_starts) != 0:  # if we can start new runs
            newsolutions.extend(new_run_starts)  # add the newly started runs

        if n > 1:  # only start looping over solutions if we've actually found solutions

            #first we populate the solutions to loop over by first adding groups
            #so we can loop over any leftover tiles
            loop_solutions = solutions.copy()
            for solution in solutions:
                # for every solution, add groups if possible
                solutions_with_groups = self.find_new_groups(n, solution['hand'], solution)
                loop_solutions.extend(solutions_with_groups)  # add the new solutions to loop_solutions
                newsolutions.extend(solutions_with_groups)  # add to the final solutions

                # for every solution, start new runs in them as well
                solutions_with_new_runs = self.start_new_runs(solution['hand'], n, solution)
                loop_solutions.extend(solutions_with_new_runs)
                newsolutions.extend(solutions_with_new_runs)
            for solution in loop_solutions:  # for every solution found so far
                newsolutions.extend(self.extend_runs(solution, n))  # extend the runs, add them to newsolutions

        if n < self.sg.numbers-1:
            return self.solution_finder(n + 1, newsolutions, tiles)
        else:
            return newsolutions

    def find_new_groups(self, n, tiles, input_solution=None):
        '''this function finds all new groups, adds them to a new solution, and returns a list of solutions
        if any tiles are duplicate, we also add a solution in which we use the duplicate tiles in a new run'''
        if input_solution is not None: #if we are working with an input solution
            if not self.check_validity(n, input_solution): #check the validity of the input_solution
                return [] #if it is invalid, return empty list
        tempsolutions = []

        filtertiles = list(filter(lambda tile: (tile[1] == n or tile[0] == self.sg.colors+1), tiles))  # keep only the tiles with value equal to n
        if len(filtertiles) > 2:
            # here we find groups at the current value, and append them to a new solution
            unique_tiles = list(set(filtertiles))  # new list with all unique tiles
        else:
            return []
        if len(filtertiles) > len(unique_tiles):
            duplicate_tiles = list(set([i for i in filtertiles if filtertiles.count(i) > 1]))  # new list with all dupes
            duplicates = True
        else:
            duplicates = False
        if len(unique_tiles) > 2:  # groups have to be at least 3 tiles long, if we don't have more than 2 unique tiles, no groups are possible
            for i in range(3, self.sg.colors+1):  # for lengths 3 and 4
                for item in combinations(filtertiles, i):  # for every combination of tiles
                    tempitem = list(item) #covert the item to a list temporarily
                    solution = defaultdict(list) #make a new solution
                    if not self.is_set_group(tempitem):
                        continue

                    if input_solution is None:  # if we are not working with an input solution:
                        solution['sets'] += [tempitem]
                        solution['hand'] += self.copy_list_and_delete_tiles(tempitem, tiles)
                    else:
                        solution['sets'] = input_solution['sets'].copy()
                        solution['sets'] += [tempitem]
                        solution['hand'] = self.copy_list_and_delete_tiles(tempitem, tiles)
                    solution['score'] = self.calculate_score(solution['sets'])
                    tempsolutions.append(solution)
        return tempsolutions

    def find_all_groups(self, tiles):
        groups = []

        for i in range(1,self.sg.numbers+1):
            groups.extend(self.find_all_groups_with_n(tiles,i))
        return groups
    
    def find_all_groups_with_n(self,tiles,n):
        groups = []
        filtertiles = list(filter(lambda tile: (tile[1] == n or tile[0] == self.sg.colors+1), tiles))  # keep only the tiles with value equal to n
        if len(filtertiles) < 3:
            return []
        for i in range(3, self.sg.colors+1):  # for lengths 3 and 4
            for item in combinations(filtertiles, i):  # for every combination of tiles
                tempitem = list(item) #covert the item to a list temporarily
                if self.is_set_group(tempitem):
                    groups.append(tempitem)
        return groups

    def extend_runs(self, solution, n):
        '''In this function we try to extend runs for a given solution and a given n value.'''
        extended_run_solutions = []
        solution_tiles = list(filter(lambda tile: (tile[1] == n or tile[0] == self.sg.colors+1),
                                     solution['hand']))  # select only the n value tiles and jokers in hand
        #here we check wether the solution we're currently trying contains valid, extendable sets.
        #we do so by checking if the unfinished sets in the solution are still extendable at the current n value
        #if not, we do not return that solution
        #this makes the algorithm significantly faster
        if not self.check_validity(n, solution):
            return []

        if len(solution_tiles) > 0:  # if we have any tiles leftover
            for tile_set in solution['sets']:  # for every set in the current solution
                tempsolution = defaultdict(list)  # create a new solution
                tempsolution['sets'] = solution['sets'].copy()
                # here we try to extend a run, if we do, we append the solution
                if not self.is_set_group(tile_set):  # if current set is not a group
                    for tile in solution_tiles:  # for every tile in hand with current n value
                        if self.can_extend(tile, tile_set):  # check if the set can be extended
                            # extend it:
                            newset = tile_set.copy()
                            newset.append(tile)  # extend the set
                            solution_tiles.remove(tile)  # remove the tile
                            tempsolution['sets'].remove(tile_set)
                            tempsolution['sets'] += [newset]  # append the new set to the solution
                            tempsolution['hand'] = self.copy_list_and_delete_tiles(tile, solution[
                                'hand'])  # remove the used tile from hand
                            tempsolution['score'] = self.calculate_score(tempsolution['sets'])  # calculate score
                            extended_run_solutions.append(tempsolution)  # append the new solution to list of solutions
                            break  # if we've extended a set, no need to check other tiles
                else:
                    continue
            tempsolution['score'] = self.calculate_score(tempsolution['sets'])  # calculate score
            if tempsolution['score'] != 0:
                extended_run_solutions.append(tempsolution)  # append the new solution to list of solutions
        return extended_run_solutions

    def start_new_runs(self, tiles, n, input_solution=None):
        '''In this function we start new runs.'''
        new_runs = []
        filtertiles = list(filter(lambda tile: (tile[1] == n or tile[0] == self.sg.colors+1), tiles)) #select only tiles of value n, or jokers

        #here we check again wether the solution we are working with is still valid
        #if not, we don't return it and we don't try to start new runs in it, as it can never become valid
        #this reduces the amount of useless solutions we try to start new runs in

        if input_solution is not None: #if we are working with an input solution
            if not self.check_validity(n, input_solution): #check the validity of the input_solution
                return [] #if it is invalid, return empty list

        for i in range(1, len(filtertiles)+1): #for length of combinations from 1 to length of the filtertiles:
            for item in combinations(filtertiles, i): #find every combination with length i
                tempsolution = defaultdict(list) #make a new solution
                tempitem = list(item) #convert the combination to a list
                if input_solution == None: #if there's no inputted solution
                    if len(item) == 1: #if there's only one tile
                        set_to_append = [tempitem]
                    else:
                        set_to_append = []
                        for j in range(0, len(tempitem)):
                            set_to_append.append([tempitem[j]]) #we need to do this to keep correct formatting

                    tempsolution['sets'] += set_to_append
                    tempsolution['hand'] = self.copy_list_and_delete_tiles(set_to_append, tiles)
                    tempsolution['score'] = self.calculate_score(tempsolution['sets'])
                    new_runs.append(tempsolution) #append the found solution
                else: #if there is an input solution
                    tempsolution['sets'] = input_solution['sets'].copy() #copy the sets in the solution into the new solution-set
                    if len(item) == 1:
                        set_to_append = [tempitem]
                    else:
                        set_to_append = []
                        for j in range(0, len(tempitem)):
                            set_to_append.append([tempitem[j]])
                    tempsolution['sets'] += set_to_append
                    tempsolution['hand'] = self.copy_list_and_delete_tiles(set_to_append, input_solution['hand'])
                    tempsolution['score'] = self.calculate_score(tempsolution['sets'])
                    new_runs.append(tempsolution)
        return new_runs

    @staticmethod
    def check_validity(n, input_solution,joker_color=6):
        '''this returns True if the solution can still become valid, false if it can't'''
        output = True
        for set in input_solution['sets']:  # for every set in that solution
            if len(set) < 3:  # if the set has 2 or less tile
                if set[-1][0] == joker_color:  # if the last tile of the set is a joker
                    if len(set) == 1:
                        continue
                    elif set[-2][0] == joker_color:
                        continue
                    elif n - set[-2][1] > 3:  # if the tile before that is 3 below the current n (not extendable anymore
                        output = False  # return an empty list, do not make new runs
                elif n - set[-1][1] > 2:  # if the last tile of the set is 2 below the current n (not extendable anymore)
                    output = False  # return an empty list, do not make new runs
        return output
    @staticmethod
    def can_extend(tile, set,joker_color=6):
        '''This function returns true if the inputted tile can extend the inputted set, otherwise returns false'''
        if tile[0] == joker_color and set[-1][0] == joker_color: #jokers can always extend other jokers
            return True
        if tile[0] == joker_color and set[-1][1] < 15: # jokers can always extend a run, but cannot be used as 16's, as they dont exist
            return True
        if len(set) == 1 and set[0][0] == joker_color and tile[1] > 1: #if a run exists with only a joker in it, extendable if tile > 1
            return True
        elif set[0][0] != tile[0]:  # if the tile is not the same suit as the first tile of the set (which is never a joker)
            return False
        elif set[-1][1] == tile[1] - 2:  # if the value of the last tile in the set is two lower than the tile, set is extendable
            return True
        elif set[-1][0] == joker_color:  # if the last tile of the set is a joker
            if set[-2][0] == joker_color: # if the tile before that is also a jjoker
                if len(set) > 2:
                    if set[-3][1] == tile[1]-3:
                        return True
            elif set[-2][1] == tile[1] - 2:  # if the tile before the joker has the same value as the tile-2, set is extendable
                return True

        else:  # set is not extendable
            return False

    @staticmethod
    def is_set_group(tiles,colors=5):
        '''This function returns true if the given set is a group, otherwise returns false'''
        if len(tiles) < 3:  # groups are always at least 3 tiles long, so if its shorter, it's a run
            return False
        if len(tiles) > colors:
            return False
        joker_color = colors+1
        # Since we never use jokers at the outside of groups unless its a game winning move,
        # if the first and last tile of a set are of equal value, its a group.
        color_set = set()
        value_set = set()
        joker_num = 0

        for tile in tiles:
            if tile[0] == joker_color:
                joker_num = joker_num+1
            else:
                color_set.add(tile[0])
                value_set.add(tile[1])
        if len(color_set)+joker_num != len(tiles):
            return False
        if len(value_set)>1:
            return False
        return True
    
    @staticmethod
    def find_all_runs(tiles):
        '''
        find all legal runs from the given tiles.
        '''
        color_dict = {}
        for tile in tiles:
            color = tile[0]
            if color not in color_dict:
                color_dict[color] = []
            color_dict[color].append(tile)
        
        runs = []

        for color, tiles_list in color_dict.items():
            sorted_tiles = sorted(tiles_list, key=lambda x: x[1])
            tempruns = []
            for i in range(len(sorted_tiles)):
                current_tile = sorted_tiles[i]
                for current_run in tempruns:
                    prev_tile = current_run[-1]
                    if current_tile[1] - prev_tile[1] == 2:
                        current_run.append(current_tile)
                        if(len(current_run)>=3):
                            runs.append(current_run.copy())
                tempruns.append([current_tile])
        return runs

    @staticmethod
    def find_all_sub_solutions(solutions, n):
        print("find_all_sub_solutions")
        sub_solutions = []
        SolveTiles.subset_helper(solutions, n, [], sub_solutions)
        return sub_solutions

    @staticmethod
    def subset_helper(solutions, n, current_subset, sub_solutions):
        if n == 0:  
            sub_solutions.append(current_subset)
            return
        if len(solutions) == 0 or n < 0:  
            return
        
        solution = solutions[0]
        remaining_solutions = solutions[1:]
        
        if len(solution) <= n:
            SolveTiles.subset_helper(remaining_solutions, n - len(solution), current_subset + [solution], sub_solutions)
        
        SolveTiles.subset_helper(remaining_solutions, n, current_subset, sub_solutions)

    def check_play(self,board,tiles):
        '''
        Check if the given tiles can all be played on the current board state.
        '''
        SolveTiles.begin_time = time.time()
        solution = []
        solution,play_tiles = self.find_play(board,tiles,n=2,play_type=CHECK_PLAY)
        return solution

    def find_solution(self,board_tiles,tiles,solution=[],play_type=NORMAL_PLAY):
        '''
        Find a valid solution from the given tiles based on the current board state.
        '''          
        if self.is_valid_new_solution(solution,board_tiles,tiles,play_type=play_type):
                return True
        if time.time()-SolveTiles.begin_time>SolveTiles.max_search_time:
            return False
        if(not tiles or len(tiles)<3):
            return False

        combinations = self.find_all_combinations(tiles)
        if combinations==[]:
            return False
        for c in combinations:
            solution.append(c)
            if self.find_solution(board_tiles,subtract_tiles(tiles,c),solution,play_type):
                return True
            elif len(solution)>0:
                solution.pop()
        return False

    def is_valid_new_solution(self,solution,board_tiles,tiles,play_type=NORMAL_PLAY):
        '''
        Check if the given solution is legal as a new solution.
        '''
        if self.is_solution_contain_all_tiles(solution,board_tiles) and count_tile_in_solution(solution)>len(board_tiles):
            if play_type==NORMAL_PLAY:
                return True
            elif play_type==CHECK_PLAY and len(tiles)==0:
                return True
            elif play_type==INITIAL_MELD_PLAY:
                score = sum([tile[1] for tile in tiles_in_solution(solution)])
                if score>=30:
                    return True
        return False


    def is_solution_contain_all_tiles(self,solution,tiles):
        '''
        This function takes a solution and a list of tiles as input. 
        It checks if the solution contains all of the tiles provided.
        '''
        solution_tiles = tiles_in_solution(solution)
        remain_tiles = subtract_tiles(solution_tiles,tiles)
        return len(remain_tiles)+len(tiles)==len(solution_tiles)
            
    def find_all_combinations(self,tiles):
        '''
        Find all legal groups and runs from current set of tiles.
        '''
        solutions = []
        runs = self.find_all_runs(tiles)
        solutions.extend(runs)
        groups = self.find_all_groups(tiles)
        solutions.extend(groups)
        return solutions

    def find_play(self,board,tiles,n=2,play_type=NORMAL_PLAY):
        '''
        Find legal combinations of tiles to play from the current set of tiles.
        '''
        SolveTiles.begin_time = time.time()
        sub_solutions = []
        if(len(board)<=n):
            sub_solutions.append(board.copy())
        else:
            sub_solutions = combinations(board,n)
        for s in sub_solutions:
            s_tiles = tiles_in_solution(s)
            hand_tiles = [tile for tile in tiles]
            hand_tiles.extend(tiles_in_solution(s))
            solution = []
            if self.find_solution(s_tiles,hand_tiles,solution,play_type):
                new_solution = subtract_solution(board,s)
                new_solution.extend(solution)
                board_tiles = tiles_in_solution(board)
                solution_tiles = tiles_in_solution(new_solution)
                item = subtract_tiles(solution_tiles,board_tiles)
                # print("tiles",tiles)
                # print("board",board)
                # print("solution",solution)
                # print("new_solution",new_solution)
                # print("s",s)
                # print("play_tiles",item)
                return new_solution,item
        return None,None
    
    def initial_meld(self,tiles):
        '''
        Find the initial meld solution.
        '''
        solutions = []
        groups = self.find_all_groups(tiles)
        solutions.extend(groups)
        runs = self.find_all_runs(tiles)
        solutions.extend(runs)
        index = 0
        max_len = 0
        for i in range(solutions):
            if len(solutions[i])>max_len:
                max_len = len(solutions[i])
                index = i
        return solutions[i]

    def compare_two_solutions(self,solution1,solution2):
        '''
        Compare two solutions to check if they contain the same tiles.
        '''
        tiles1 = []
        tiles2 = []
        for tiles in solution1:
            tiles1.extend(tiles)
        for tiles in solution2:
            tiles2.extend(tiles)
        tiles1 = sorted(tiles1,key=compare_func)
        tiles2 = sorted(tiles2,key=compare_func)
        if len(tiles1) != len(tiles2):
            return False
        for i in range(len(tiles1)):
            if tiles1[i][0]!=tiles2[i][0] or tiles1[i][1]!=tiles2[i][1]:
                return False
        return True
        

    @staticmethod
    def calculate_score(hand,joker_color=6):
        '''this function calculates the score for a given hand'''
        score = 0
        for set in hand:
            if len(set) > 2:
                for tile in set:
                    if tile[0] != joker_color: #jokers do not award points
                        score += tile[1] #score is the value of all tiles combined
            else:  # if any set is not longer than two, solution awards no score
                score = 0
                return score
        return score

    @staticmethod
    def copy_list_and_delete_tiles(to_remove, tiles):
        '''This function takes to_remove as input and removes the contents from tiles
            Mostly used to strip used tiles from hand.'''
        if to_remove is None:  # if nothing has to be removed, return the tiles
            return tiles
        else:
            templist = tiles.copy()  # make a copy of the tiles
            if type(to_remove) is tuple:  # if we remove just a single tile
                templist.remove(to_remove)
                return templist
            else:  # if to_remove is a list of tiles to remove
                for tile in to_remove:
                    if type(tile) is tuple:
                        templist.remove(tile)
                    else:
                        for tupletile in tile:
                            templist.remove(tupletile)
                return templist
