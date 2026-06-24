import pygame as pg 

from files.ui.av import to_AV

av = to_AV((64, 64))

csb = av.ChatSideBar()

csb.receive_text('hello my love', player_index=1)

csb.entry.register_text('how do you do my love')
csb.entry_view.set_reference(csb.entry.surface)

csb.draw()

pg.image.save(csb.surface, 'csb.png')


