# Demetre Seturidze
# Chess
# Server

import asyncio, websockets, uuid, time
from typing import List, Dict
from files.logic.serialization import serialize, deserialize
from files.logic.sets import Set
from files.media.assets import Assets
import random


RAISE = False 


# hosts a game        
class GameServer:
    def __init__(self, set : Set, num_players = 2):
        self.players : List[websockets.ClientConnection | None] = [None] * num_players
        self.player_dict : Dict[str, int] = {}

        self.set = set
        self.game = None 

        self.num_joined = 0
        self.num_players = num_players

        self.available_spots = [i for i in range(num_players)]

        self.enforce_player = False

        self.lock = asyncio.Lock()


    def assign(self, ws, id : str) -> int:
        if self.num_joined == self.num_players:
            raise Exception('All players already assigned')
        
        elif self.player_dict:
            index = self.player_dict.get(id, -1)
            if index != -1 and self.players[index] == None:
                self.players[index] = ws 
                self.available_spots.remove(index)

                self.num_joined += 1
                return index
            
        random.shuffle(self.available_spots)
        index = self.available_spots.pop()

        self.players[index] = ws
        self.player_dict[id] = index 

        self.num_joined += 1
        return index
    

    async def safe_send(self, index : int, msg : str, timeout : float | None = None, wait : bool = False):
        if wait:
            wait_condition = True
            start = time.time()
            while wait_condition:
                if timeout is not None and time.time() - start > timeout:
                    return 
                await asyncio.sleep(1)
                async with self.lock:
                    wait_condition = self.num_joined != self.num_players
            
        async with self.lock:
            player = self.players[index]
            if player is not None:
                await player.send(msg)

    async def safe_send_except(self, index : int, msg : str, timeout : float | None = None, wait : bool = False):
        if wait:
            wait_condition = self.num_joined != self.num_players
            start = time.time()
            while wait_condition:
                if timeout is not None and time.time() - start > timeout:
                    return 
                await asyncio.sleep(1)
                async with self.lock:
                    wait_condition = self.num_joined != self.num_players
        
        async with self.lock:
            for i in range(self.num_players):
                player = self.players[i]
                if i != index and player is not None:
                    await player.send(msg)

    # establishes connection and returns integer index
    async def establish(self, ws : websockets.ClientConnection) -> int:
        id = await ws.recv()
            
        async with self.lock:
            index = self.assign(ws, id)
            # send the player index 
            await ws.send(str(index))
            # send 1 if player side is enforced, 0 else
            await ws.send(str(self.enforce_player))
            # send the relevant set 
            await ws.send(serialize(self.set))

            if self.game is None:
                self.game = self.set()
            
            await ws.send(serialize(self.game))
        
        print(f'[CONNECT] {id}')
        return index 
    
    async def disconnect(self, index : int):
        async with self.lock:
            if self.players[index] is None:
                return 
            
            id = self.players[index].id
            self.players[index] = None 
            self.num_joined -= 1
            self.available_spots.append(index)
        
        print(f'[DISCONNECT] {id}')
        

    async def handler(self, ws : websockets.ClientConnection):
        index = None
        try:
            index = await self.establish(ws)

            async for message in ws:
                cmd = deserialize(message)
                if isinstance(cmd, Event):

                    # if this is reset, then we reset
                    if cmd.label == 'reset':
                        async with self.lock:
                            self.game = self.set()

                    # if this is an action, we update the server's board.
                    if cmd.label == 'action':
                        async with self.lock:
                            self.game.register_action(cmd.action)

                    if cmd.label == 'quit':
                        await ws.close(reason=cmd.label)
                        await self.disconnect(index)
                        return

                    # Relay message to other players, if not None
                    if cmd.label != 'none':
                        await self.safe_send_except(index, message)

        except Exception as e:
            print(f'[EXCEPTION] {e}')
        finally:
            if index is not None:
                await self.disconnect(index)
            

    async def run(self, host : str = 'localhost', port : int = 8888, enforce_player = False):
        self.enforce_player = enforce_player
        async with websockets.serve(self.handler, host, port):
            await asyncio.Future() 



from files.system.environment import GameWindow
from files.logic.game import Event, Game
import pygame as pg

class GameClient:
    def __init__(self, assets : Assets, id : str | None = None):
        self.sound_lock = asyncio.Lock()
        self.instance_lock = asyncio.Lock()
        self.queue_lock = asyncio.Lock()

        self.id = str(uuid.uuid1()) if id is None else id
        self.assets = assets 
        self.sounds : List[str] = []

        # list of things to send 
        self.queue : List[Event] = []
        self.instance = None

    async def prime(self):
        async with self.instance_lock:
            board = self.instance.board 
        
        pg.display.init()
        self.screen = pg.display.set_mode((board.width, board.height))
        board.play('start')
    
    # establishes the connection:
    # sends client id, receives player index, set, and the game 
    async def establish(self, ws : websockets.ClientConnection):
        # send client information
        await ws.send(self.id)
        print('[CONNECT]')

        # receive the player index 
        self.index = int(await ws.recv())
        enforce_player = bool(await ws.recv())

        # receive the set
        set_obj = deserialize(await(ws.recv()))

        # receive the serialized game object
        game_obj = deserialize(await(ws.recv()))

        # construct the instance
        self.instance = GameWindow(set_obj, assets=self.assets, player_index=self.index, enforce_player=enforce_player)
        self.instance.game = game_obj
        await self.prime()


    async def sender(self, ws : websockets.ClientConnection):
        while True:
            await asyncio.sleep(0.5)
            async with self.queue_lock:
                for _ in range(len(self.queue)):
                    cmd = self.queue.pop()
                    label = cmd.label
                    cmd = serialize(cmd)
                    
                    if label != 'none':
                        print(f'SEND :: {cmd}')
                        await ws.send(cmd)
                    
                    if label == 'quit':
                        await ws.close(reason=label)
                        await ws.recv()


    
    # listens to events from the socket
    async def listener(self, ws : websockets.ClientConnection):
        async for message in ws:
            print(f'RECV :: {message}')
            obj = deserialize(message)

            if isinstance(obj, Event):
                async with self.instance_lock:
                    event = self.instance.register(obj)
                async with self.sound_lock:    
                    self.sounds.extend(event.sounds)
            
            elif isinstance(obj, Game):
                async with self.instance_lock:
                    self.instance.begin(game=obj)

    async def play_listened_sounds(self):
        while True:
            await asyncio.sleep(0.2)
            async with self.sound_lock:
                if self.sounds:
                    for sound in self.sounds:
                        self.instance.board.play(sound)
                    self.sounds = []

    async def main_loop(self):
        # keeps track of loop parameters to be able to modularize the event loop.
        # this thing gets passed around and edited in-place as opposed to holding
        # all variables locally inside the run function
        running = True

        while running:
            async with self.instance_lock:
                event = self.instance.frame(self.screen)
            async with self.queue_lock:
                self.queue.append(event)

            await asyncio.sleep(0)

            pg.display.flip()

    # listens for events from the server, handles accordingly
    async def run(self, host : str = 'localhost', port : int = 8888):
        try:
            async with websockets.connect(f"ws://{host}:{port}") as ws:
                await self.establish(ws)
                await asyncio.gather(self.sender(ws), self.listener(ws), self.play_listened_sounds(), self.main_loop())
        except websockets.exceptions.ConnectionClosed as e:
            print(f"[DISCONNECT] code={e.code}, reason={e.reason}")



