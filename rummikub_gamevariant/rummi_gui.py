import pygame
from pygame.locals import *
import sys
import random
import time
from game_engine import RummikubGame
from player import Player
from button import Button
import traceback
import threading
from util import subtract_tiles

TILE_WIDTH = 50
SMALL_TILE_WIDTH = 35
TILE_HEIGHT = 60
SMALL_TILE_HEIGHT = 45
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 900
MAX_SEARCH_TIME = 30
MIN_PLAY_TIME = 3

def compare_func(tile):
    return tile[0]*15 + tile[1]

class RummiGui:
    def __init__(self,computer_num=1):
        pygame.init()
        pygame.font.init()
        
        #pygame.mixer.init()
        self.screen = pygame.display.set_mode([WINDOW_WIDTH,WINDOW_HEIGHT])
        self.colors = ['Black','Blue','Cyan','Red','Yellow','Joker']

        pygame.display.set_caption('Rummi')
        self.game = RummikubGame()
        self.background_color = (20, 20, 55)
        self.players = []
        self.players.append(Player(rack=self.game.draw_tile(rack=[],tile_amount=14)))

        for i in range(computer_num):
            self.players.append(Player(rack=self.game.draw_tile(rack=[],tile_amount=14),auto_play=True))
        self.load_images()
        self.show_all_tile = False
        self.buttons = []

        play_button = Button("Play",pygame.Rect(750,700,40,30))
        play_button.perform_mouse_up = self.do_play
        self.buttons.append(play_button)

        show_all_tile_button = Button("Show All Tiles",pygame.Rect(800, 700, 60, 30))
        show_all_tile_button.perform_mouse_up = lambda: (
            setattr(self, 'show_all_tile', not self.show_all_tile)
        )
        self.buttons.append(show_all_tile_button)

        play_for_me_button = Button("Play For Me",pygame.Rect(870,700,60,30))
        play_for_me_button.perform_mouse_up = lambda: (
            setattr(self, 'auto_play', not self.auto_play)
        )
        self.buttons.append(play_for_me_button)

        draw_tile_button = Button("Draw Tiles",pygame.Rect(940,700,60,30))
        draw_tile_button.perform_mouse_up = self.draw_tile
        self.buttons.append(draw_tile_button)

        new_round_button = Button("New Round",pygame.Rect(500,500,60,30))
        new_round_button.perform_mouse_up = self.new_round
        new_round_button.show = False
        new_round_button.enable = False
        self.buttons.append(new_round_button)

        self.font = pygame.font.SysFont(None, 12)

        self.running = True
        self.current_player = random.randrange(0,len(self.players))
        self.auto_play = False
        self.thinking = False
        self.thinking_positions = [pygame.Rect(580,630,30,30),pygame.Rect(170,430,30,30),pygame.Rect(580,150,30,30),pygame.Rect(1000,430,30,30)]

        self.selected_tiles=[]
        self.candidate_tiles = []
        self.status = 0
        self.begin_thinking_time = int(time.perf_counter())
        
    def load_images(self):
        '''
        Load tile images from disk.
        '''
        self.images = [] # tile images
        self.small_images = [] # small tile images draw on the table
        for i in range(len(self.colors)-1):
            tile_images = []
            small_tile_images = []
            for j in range(1,16):
                tile_image = pygame.image.load(f'images/{self.colors[i]}_{j}.png').convert_alpha()
                tile_image = pygame.transform.scale(tile_image, (TILE_WIDTH, TILE_HEIGHT))
                small_tile_image = pygame.transform.scale(tile_image, (SMALL_TILE_WIDTH, SMALL_TILE_HEIGHT))
                tile_images.append(tile_image)
                small_tile_images.append(small_tile_image)
            self.images.append(tile_images)
            self.small_images.append(small_tile_images)
        joker_images = []
        small_joker_images = []
        for j in range(1,3):
            joker_image = pygame.image.load(f'images/Joker_{j}.png').convert_alpha()
            joker_image = pygame.transform.scale(joker_image, (TILE_WIDTH, TILE_HEIGHT))
            small_joker_image = pygame.transform.scale(joker_image, (SMALL_TILE_WIDTH, SMALL_TILE_HEIGHT))
            joker_images.append(joker_image)
            small_joker_images.append(small_joker_image)
        self.images.append(joker_images)
        self.small_images.append(small_joker_images)

        back_image = pygame.image.load(f'images/back.png').convert_alpha()
        back_image = pygame.transform.scale(back_image, (TILE_WIDTH, TILE_HEIGHT))
        self.tile_back_image = back_image

    def turn_next_player(self):
        '''
        This function updates the turn order and allows the next player in the rotation to make their move.
        '''
        if(self.status==100):
            return
        self.begin_thinking_time = int(time.perf_counter())
        self.current_player = (self.current_player+1)%len(self.players)

    def draw_bottom_rack(self,rack):
        '''
        Draw the tiles held by the human player at the bottom of the game screen.
        rack: The rack that represents the tiles held by the human player.
        '''
        left_span = (WINDOW_WIDTH-(TILE_WIDTH+2)*15)/2
        top_span = WINDOW_HEIGHT-TILE_HEIGHT*2.5
        for i in range(len(rack)):
            tile = rack[i]
            x = left_span+(i%15)*(TILE_WIDTH+2)
            y = top_span + (i//15)*(TILE_HEIGHT+2)
            self.screen.blit(self.images[tile[0]-1][tile[1]-1],(x,y))

    def draw_candidate_tiles(self):
        '''
        Draws two tiles from the draw pile and presents them to the user for selection.
        '''
        left_span = (WINDOW_WIDTH-(TILE_WIDTH+2)*2)/2
        top_span = WINDOW_HEIGHT-TILE_HEIGHT*3.8
        rack = self.candidate_tiles
        for i in range(len(rack)):
            tile = rack[i]
            x = left_span+i*(TILE_WIDTH+2)
            y = top_span
            self.screen.blit(self.images[tile[0]-1][tile[1]-1],(x,y))

    def draw_left_rack(self,rack):
        '''
        Draw the tiles held by the computer at the left of the game screen.
        rack: The rack that represents the tiles held by the left computer.
        '''
        left_span = TILE_WIDTH*2.5
        top_span = (WINDOW_HEIGHT-(TILE_HEIGHT+2)*10)/2
        for i in range(len(rack)):
            tile = rack[i]
            y = top_span+(i%10)*(TILE_HEIGHT+2)
            x = left_span - (i//10)*(TILE_WIDTH+2)
            if self.show_all_tile:
                self.screen.blit(self.images[tile[0]-1][tile[1]-1],(x,y))
            else:
                self.screen.blit(self.tile_back_image,(x,y))

    def draw_top_rack(self,rack):
        '''
        Draw the tiles held by the computer at the top of the game screen.
        rack: The rack that represents the tiles held by the top computer.
        '''
        left_span = (WINDOW_WIDTH-(TILE_WIDTH+2)*15)/2
        top_span = TILE_HEIGHT*0.5
        for i in range(len(rack)):
            tile = rack[i]
            x = left_span+(i%15)*(TILE_WIDTH+2)
            y = top_span + (i//15)*(TILE_HEIGHT+2)
            if self.show_all_tile:
                self.screen.blit(self.images[tile[0]-1][tile[1]-1],(x,y))
            else:
                self.screen.blit(self.tile_back_image,(x,y))

    def draw_right_rack(self,rack):
        '''
        Draw the tiles held by the computer at the right of the game screen.
        rack: The rack that represents the tiles held by the right computer.
        '''
        left_span = WINDOW_WIDTH-TILE_WIDTH*2.5
        top_span = (WINDOW_HEIGHT-(TILE_HEIGHT+2)*10)/2
        for i in range(len(rack)):
            tile = rack[i]
            y = top_span+(i%10)*(TILE_HEIGHT+2)
            x = left_span + (i//10)*(TILE_WIDTH+2)
            if self.show_all_tile:
                self.screen.blit(self.images[tile[0]-1][tile[1]-1],(x,y))
            else:
                self.screen.blit(self.tile_back_image,(x,y))

    def check_select_tiles(self):
        '''
        Check which tile the user has clicked on and adds it to the list of selected tiles for the next move.
        '''
        mouse_pos = pygame.mouse.get_pos()
        left_span = (WINDOW_WIDTH-(TILE_WIDTH+2)*15)/2
        top_span = WINDOW_HEIGHT-TILE_HEIGHT*2.5
        rack = self.players[0].rack
        for i in range(len(rack)):
            tile = rack[i]
            x = left_span+(i%15)*(TILE_WIDTH+2)
            y = top_span + (i//15)*(TILE_HEIGHT+2)
            rect = pygame.Rect(x,y,TILE_WIDTH,TILE_HEIGHT)
            if(rect.collidepoint(mouse_pos)):
                if i not in self.selected_tiles:
                    self.selected_tiles.append(i)
                else:
                    self.selected_tiles.remove(i)
        
        # select the candidate 2 tiles draw from deck
        left_span = (WINDOW_WIDTH-(TILE_WIDTH+2)*2)/2
        top_span = WINDOW_HEIGHT-TILE_HEIGHT*3.8
        rack = self.candidate_tiles
        for i in range(len(rack)):
            tile = rack[i]
            x = left_span+i*(TILE_WIDTH+2)
            y = top_span
            rect = pygame.Rect(x,y,TILE_WIDTH,TILE_HEIGHT)
            if(rect.collidepoint(mouse_pos)):
                self.players[0].add_tile(tile)#add selected tile to player's rack
                #return the other tile to the game deck
                if(i==0):
                    self.game.return_tile(self.candidate_tiles[1])
                else:
                    self.game.return_tile(self.candidate_tiles[0])
                self.candidate_tiles.clear()
                self.turn_next_player()
                break

    def draw_selected_tiles(self):
        '''
        Draw a small green point on the selected tiles
        '''
        left_span = (WINDOW_WIDTH-(TILE_WIDTH+2)*15)/2
        top_span = WINDOW_HEIGHT-TILE_HEIGHT*2.5
        rack = self.players[0].rack
        for i in self.selected_tiles:
            if(i>=len(rack)):
                break
            tile = rack[i]
            x = left_span+(i%15)*(TILE_WIDTH+2)
            y = top_span + (i//15)*(TILE_HEIGHT+2)
            pygame.draw.rect(self.screen, pygame.Color("green"), pygame.Rect(x+TILE_WIDTH/2-4,y,8,8), 4)

    def computer_play(self):
        '''
        Automatically play tiles for the current player.
        If the 'auto_play' flag is set to true, it can also play tiles for the human player.
        '''
        self.thinking = True
        player = self.players[self.current_player]
        if(self.current_player==0):
            self.selected_tiles.clear()
        rack=[]
        # If the player has not played any tiles yet, they must perform an initial_meld first.
        if(player.status==0):
            rack, self.game.board = self.game.initial_meld(self.game.board, player.rack.copy())
            if len(rack)==len(player.rack):
                rack = self.game.draw_tile(player.rack)
            else:
                player.status=1
        else:
            # play tiles normally
            rack, self.game.board = self.game.take_computer_turn2(self.game.board, player.rack)
            if(len(rack)==len(player.rack)) and len(self.game.bag)==0:
                player.status = 100
        if time.perf_counter()-self.begin_thinking_time<MIN_PLAY_TIME:
            time.sleep(time.perf_counter()-self.begin_thinking_time<MIN_PLAY_TIME)
        player.update_rack(rack)
        self.turn_next_player()
        
        self.thinking = False

    def do_play(self):
        '''
        Do play action for the human player
        '''
        if(self.current_player!=0 or self.auto_play):
            return
        if(self.players[0].status==0):
            self.computer_play()
            return 
        play_tiles = []
        if(len(self.selected_tiles)==0):
            print("Please select tiles!")
            return
        for i in self.selected_tiles:
            play_tiles.append(self.players[0].rack[i])
        s = self.game.check_play(play_tiles)
        if s:
            self.game.board = s
            self.players[0].update_rack(subtract_tiles(self.players[0].rack,play_tiles))
            self.selected_tiles.clear()
            self.turn_next_player()
        else:
            print("The selected tiles do not conform to the rules for playing.")
            print("board",self.game.board)
            print("play_tile",play_tiles)
    
    def draw_tile(self):
        '''
        Do draw tile action for the human player
        '''
        if(self.current_player!=0 or self.auto_play):
            return
        if(len(self.candidate_tiles)!=0):
            print("Please choose one tile")
            return
        self.candidate_tiles = self.game.draw_tile([],tile_amount=2)
    
    def new_round(self):
        '''
        Reset the game and start a new round.
        '''
        self.game.reset()
        self.status = 0
        for player in self.players:
            player.reset()
            player.update_rack(self.game.draw_tile([],tile_amount=14))
        for button in self.buttons:
            if button.text =="New Round":
                button.show = False
                button.enable = False
            else:
                button.show=True
                button.enable=True

    def draw_center_board(self,board):
        '''
        Draw tiles on the table.
        '''
        max_tile = 20
        left_span = (WINDOW_WIDTH-(SMALL_TILE_WIDTH+2)*max_tile)/2
        top_span =TILE_HEIGHT*4
        row = 0
        col = 0
        tiles_num = 0
        for i in range(len(board)):
            rack = board[i]
            if(col+tiles_num+len(rack)>max_tile):
                row = row + 1
                col = 0
                tiles_num = 0
            for i in range(len(rack)):
                tile = rack[i]
                x = left_span+((tiles_num+col+i)%max_tile)*(SMALL_TILE_WIDTH+2)
                y = top_span + row*(SMALL_TILE_HEIGHT+2)
                self.screen.blit(self.small_images[tile[0]-1][tile[1]-1],(x,y))
            col = col+1
            tiles_num = tiles_num+len(rack)
    
    def draw_thinking_label(self):
        '''
        Show the remaining seconds for the current player.
        '''
        self.check_time_out()
        pygame.draw.rect(self.screen, pygame.Color("lightgray"), self.thinking_positions[self.current_player])
        text = self.font.render(str(MAX_SEARCH_TIME-int(time.perf_counter()-self.begin_thinking_time)), True, pygame.Color("black"))
        text_rect = text.get_rect(center=self.thinking_positions[self.current_player].center)
        self.screen.blit(text, text_rect)

    def draw_score(self):
        '''
        Show scores at the end of each round.
        '''
        left_span = 400
        top_span = 400
        font = pygame.font.SysFont(None, 24)

        for i in range(len(self.players)):
            text = ""
            if i == 0:
                text = text + "You   "
            else:
                text = text + "Bot"+str(i)+"  "
            if i ==self.current_player:
                text = text + "Win  "
            else:
                text = text + "Lost "
            text = text + str(self.players[i].score)
            text = font.render(text, True, pygame.Color("yellow"))
            text_rect = text.get_rect(center=(left_span+75,top_span+i*30))
            self.screen.blit(text, text_rect)

    def draw_remain_tiles(self):
        '''
        Show the number of tiles remaining in the deck.
        '''
        self.screen.blit(self.tile_back_image,((WINDOW_WIDTH-TILE_WIDTH)/2+2*TILE_WIDTH,2.5*TILE_HEIGHT))
        font = pygame.font.SysFont(None, 24)
        text = font.render(str(len(self.game.bag)), True, pygame.Color("yellow"))
        text_rect = text.get_rect(center=(WINDOW_WIDTH/2+2*TILE_WIDTH,3.4*TILE_HEIGHT))
        self.screen.blit(text, text_rect)

    def check_time_out(self):
        '''
        Check if the current player has timed out and automatically perform a action if timeout occurs.
        '''
        if(self.auto_play or self.current_player!=0):
            return
        if(time.perf_counter()-self.begin_thinking_time>MAX_SEARCH_TIME):
            if(len(self.candidate_tiles)>0):
                self.players[0].add_tile(self.candidate_tiles[0])
                self.game.return_tile(self.candidate_tiles[1])
                self.turn_next_player()
            else:
                self.computer_play()
                
    def refresh_screen(self):
        self.screen.fill(self.background_color)
        for button in self.buttons:
            button.refresh(self.screen)
        if self.status==100:
            self.draw_score()
            return

        for i in range(len(self.players)):
            if i == 0:
                self.draw_bottom_rack(self.players[i].rack)
            elif i == 1:
                self.draw_left_rack(self.players[i].rack)
            elif i == 2:
                self.draw_top_rack(self.players[i].rack)
            elif i == 3:
                self.draw_right_rack(self.players[i].rack)

        self.draw_center_board(self.game.board)
        self.draw_thinking_label()
        self.draw_selected_tiles()
        self.draw_candidate_tiles()
        self.draw_remain_tiles()
    
    def check_game_status(self):
        '''
        Check if the game has ended.
        '''
        end_num = 0
        for i,player in enumerate(self.players):
            if len(player.rack)==0:
                self.status = 100
                self.calculate_player_score()
                return
            if player.status==100:
                end_num = end_num+1
        if(end_num==len(self.players)):
            self.status = 100
            self.calculate_player_score()
    
    def calculate_player_score(self):
        '''
        Calculate the player’s score at the end of a round.
        '''
        for button in self.buttons:
            if button.text == "New Round":
                button.show = True
                button.enable = True
            else:
                button.show = False
        min_value = self.players[0].get_tiles_value()
        self.current_player = 0
        for i in range(len(self.players)):
            player = self.players[i]
            if player.get_tiles_value()<min_value:
                self.current_player = i
                min_value = player.get_tiles_value()
        win_player = self.players[self.current_player]
        for i in range(len(self.players)):
            player = self.players[i]
            if i != self.current_player:
                player.score = 0 - (player.get_tiles_value()-win_player.get_tiles_value())
                win_player.score = win_player.score - player.score

    def main(self):
        '''
        The main process of the game.
        '''
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONUP:
                    self.check_select_tiles()

                for button in self.buttons:
                    button.handle_event(event)
            if(self.status!=100):
                self.check_game_status()
            if not self.thinking:
                if self.current_player != 0 or self.auto_play:
                    thread = threading.Thread(target=self.computer_play)
                    thread.start()
            rummi.refresh_screen()
            pygame.display.flip()
            clock.tick(60)

if __name__ == '__main__':
    try:
        rummi = RummiGui(computer_num=3)
        rummi.main()
            
    except SystemExit:
        pass
    except:
        traceback.print_exc()
        pygame.quit()
