import pygame
from pygame.locals import *

class Button:

    def __init__(self,text,rect):
        self.text = text
        self.rect = rect
        self.enable = True
        self.show = True
    
    def handle_event(self,event):
        if not self.enable:
            return
        if event.type == pygame.MOUSEBUTTONUP:
            if self.rect.collidepoint(event.pos):
                self.perform_mouse_up()

    def perform_mouse_up(self):
        pass

    def refresh(self,screen):
        if not self.show:
            return
        mouse_pos = pygame.mouse.get_pos()
        font = pygame.font.SysFont(None, 12)
        
        if self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, pygame.Color("lightgray"), self.rect)
        else:
            pygame.draw.rect(screen, pygame.Color("white"),self.rect)
    
        text = font.render(self.text, True, pygame.Color("black"))
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)