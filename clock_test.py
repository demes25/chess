from files.ui.av import to_AV, pg, new_surface

av = to_AV(4)


game_side_bar = av.SideBar(8*4*16)

#pg.image.save(timer.draw(367), 'clock.png')
game_side_bar.draw([367, 129], [[(1, 'Queen'), (1, 'King'), (1, 'Rook')],[(0, 'Queen'), (0, 'King'), (0, 'Rook')]])
surface = new_surface(game_side_bar.shape)

game_side_bar.blit_onto(surface)

pg.image.save(surface, 'figarr.png')




