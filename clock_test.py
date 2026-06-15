from files.ui.av import to_AV, pg

av = to_AV((64, 64))


game_side_bar = av.GameSideBar(arr_dims=(5, 2), env_height=8)

#pg.image.save(timer.draw(367), 'clock.png')
game_side_bar.draw([367, 129], [[(1, 'Queen'), (1, 'King'), (1, 'Rook')],[(1, 'Queen'), (1, 'King'), (1, 'Rook')]])
pg.image.save(game_side_bar.surface, 'figarr.png')




