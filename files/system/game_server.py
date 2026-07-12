# Demetre Seturidze
# Chess
# Server

import asyncio, websockets, uuid
from dataclasses import dataclass
from typing import List, Dict

from netlib.serialization import serialize, deserialize
from netlib.server import Server, SenderClient, Address
from netlib import logs

from files.logic.game import Event
from files.logic.sets import GameSet
import random


RAISE = True 


# hosts a game        
class OnlineGame(Server):

    class Connection(Server.Connection):
        def __init__(self, socket : websockets.ServerConnection, id : str, index : int):
            self.id = id 
            self.index = index 
            super().__init__(socket)


    def __init__(self, game_set : GameSet, num_players : int = 2, default_time_s : float = 600, enforce_player : bool = True):
        super().__init__()

        # associates the ID of a game client to their index in the game
        self.player_dict : Dict[str, int] = {}
        self.player_list : List[OnlineGame.Connection] = [None] * num_players

        self.game_set = game_set
        self.default_time_s = default_time_s
        self.game = None 

        self.num_players = num_players

        self.available_spots = [i for i in range(num_players)]

        self.enforce_player = False

        self.lock = asyncio.Lock()
        
        self.enforce_player=enforce_player


    def assign(self, ws, id : str) -> Connection:
        if self.breadth == self.num_players:
            raise Exception('All players already assigned')
        
        index = self.player_dict.get(id, -1)
        if index != -1 and self.player_list[index] is None: 
            self.available_spots.remove(index)
        else:
            random.shuffle(self.available_spots)
            index = self.available_spots.pop()
            self.player_dict[id] = index 

        connection = OnlineGame.Connection(
                socket=ws,
                id=id,
                index=index
            )

        self.player_list[index] = connection

        return connection 
    

    # establishes connection and returns integer index
    async def establish(self, ws : websockets.ClientConnection) -> Connection:
        id = await ws.recv()
            
        async with self.lock:
            connection = self.assign(ws, id)
            
            if self.game is None:
                self.game = self.game_set.new_game(timer=self.default_time_s)

            args = serialize({
                    'index' : connection.index,
                    'enforce_player' : self.enforce_player,
                    'default_time' : self.default_time_s,
                    'set' : self.game_set,
                    'game' : self.game
                }
            )
            
        await ws.send(args)
        logs.info(self, f'Connected {id}')

        return connection
    
    async def disconnect(self, connection : Connection):
        async with self.lock:
            id = connection.id
            self.player_list[connection.index] = None 
            self.available_spots.append(connection.index)
        
        logs.info(self, f'Disconnected {id}')
    
    # registers the message, returns true if we keep going
    async def register(self, message : str, connection : Connection) -> bool:
        cmd = deserialize(message)
        
        if isinstance(cmd, Event):
            # if this is reset, then we reset and send the new game to everybody
            if cmd.label == 'reset':
                async with self.lock:
                    self.game = self.game_set.new_game(self.default_time_s)

            # if this is an action, we update the server's board.
            if cmd.label == 'action':
                async with self.lock:
                    self.game.register_action(cmd.action)

            if cmd.label == 'quit':
                with open('game.txt', 'w') as f:
                    f.write(serialize(self.game))
                await connection.close(reason=cmd.label)

            # Relay message to other players, if not None
            if cmd.label != 'none':
                for client in self.clients:
                    if client is not connection:
                        await client.send(message)
        
        return cmd.label != 'quit'

            


from files.ui.windows import GameWindow
from files.logic.game import Event, Game
from files.ui.av import AVType, to_AV, new_window
import pygame as pg

class OnlinePlayer(SenderClient):
    def __init__(self, av : AVType, id : str | None = None, send_interval : float = 0.01, sound_interval : float = 0.02, log_name : str | None = None):
        self.id = id
        self.av = to_AV(av)

        self.sound_lock = asyncio.Lock()
        self.instance_lock = asyncio.Lock()

        self.sound_interval = sound_interval
        
        # buffer for collected sounds
        self.sounds : List[str] = []
        self.instance = None

        super().__init__(send_interval, log_name=log_name)

    async def prime(self):
        async with self.instance_lock:
            w = self.instance.width
            h = self.instance.height
            board=self.instance.board
        
        icon = self.av.assets.colored_figures[0]['King']
        caption = 'OBCHESSED'

        self.screen = new_window((w, h), icon=icon, caption=caption)
        
        board.play('start')
    
    # establishes the connection:
    # sends client id, receives player index, set, and the game 
    async def establish(self, ws : websockets.ClientConnection):
        if self.id is None:
            self.id = str(ws.id)

        # send client information
        await ws.send(self.id)

        # receive the handshake
        handshake = deserialize(await ws.recv())

        # receive the player index 
        self.index = handshake['index']
        enforce_player = handshake['enforce_player']

        # receive the set
        set_obj = handshake['set']

        # receive the serialized game object
        game_obj : Game = handshake['game']

        # construct the instance
        self.instance = GameWindow(set_obj, av=self.av, player_index=self.index, enforce_player=enforce_player, default_time_s=handshake['default_time'])
        self.instance.begin(game=game_obj)
        logs.info(self, f'Connected {ws.id}')
        await self.prime()
    
    # listens to events from the socket
    async def register(self, message : str):
        logs.info(self, f'RECV :: {message}')
        obj = deserialize(message)

        if isinstance(obj, Event):
            async with self.instance_lock:
                event = self.instance.register(obj)
            async with self.sound_lock:    
                self.sounds.extend(event.sounds)
        
        elif isinstance(obj, Game):
            async with self.instance_lock:
                self.instance.begin(game=obj)
                self.instance.board.play('start')

    # sends a message to the given socket connection
    async def send(self, message : Event, ws : websockets.ClientConnection):
        cmd = serialize(message)
        logs.info(self, f'SEND :: {cmd}')
        await ws.send(cmd)

        if message.label == 'reset':
            async with self.instance_lock:
                self.instance.begin()
                self.instance.board.play('start')

        if message.label == 'quit':
            await ws.close(reason=message.label)
            await ws.recv()



    async def play_queued_sounds(self, _):
        while True:
            await asyncio.sleep(self.sound_interval)
            async with self.sound_lock:
                if self.sounds:
                    for sound in self.sounds:
                        self.instance.board.play(sound)
                    self.sounds = []

    async def ui_loop(self, _):
        # keeps track of loop parameters to be able to modularize the event loop.
        # this thing gets passed around and edited in-place as opposed to holding
        # all variables locally inside the run function
        while True:
            async with self.instance_lock:
                event = self.instance.frame(self.screen)
            
            if event.label != 'none':
                await self.queue(event)

            await asyncio.sleep(0)

            pg.display.flip()

    # listens for events from the server, handles accordingly
    async def run(self, address : Address = Address()):
        await super().run(address, loops=[self.ui_loop, self.play_queued_sounds])



