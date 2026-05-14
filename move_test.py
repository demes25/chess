from files.boards import *
import time 

queen = Figure('Queen', 9, (100, 100, 100), (50, 50), [Moves.DiagonalSpan(), Moves.OrthogonalSpan()])

board = np.zeros([8, 8])

print(np.asarray(queen.access_map(board, (4, 3)), dtype=np.int16))