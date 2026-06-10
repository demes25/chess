# Demetre Seturidze
# Chess
# Server

import asyncio, websockets, uuid
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
        
    async def new_game(self):
        assert self.num_joined == self.num_players

        self.game = self.set()
        sergame = serialize(self.game)

        for i in range(self.num_players):
            await self.players[i].send(sergame)
        

    async def handler(self, ws : websockets.ClientConnection):
        try:
            id = await ws.recv()
            index = self.assign(ws, id)

            # send the player index 
            await ws.send(str(index))
            # send the relevant set 
            await ws.send(serialize(self.set))

            if self.num_joined == self.num_players:
                self.game = self.set()

            async for message in ws:
                while self.num_joined < self.num_players:
                    asyncio.sleep(1)

                if 'reset' in message:
                    self.game = self.set()

                # Relay message to other players
                for i in range(self.num_players):
                    if i != index:
                        await self.players[i].send(message)

        finally:
            self.players[index] = None 
            self.num_joined -= 1
            self.available_spots.append(index)

    async def run(self, host : str = 'localhost', port : int = 8888):
        async with websockets.serve(self.handler, host, port):
            await asyncio.Future() 



from files.system.instance import GameInstance

class GameClient:
    def __init__(self, assets : Assets):
        self.lock = asyncio.Lock()
        self.id = str(uuid.uuid1())
        self.assets = assets 

    async def sender(self, ws : websockets.ClientConnection):
        pass
    
    async def listener(self, ws : websockets.ClientConnection):
        pass 


    async def establish(self, ws : websockets.ClientConnection):
        # send client information
        await ws.send(self.id)
        
        # receive the player index 
        self.index = int(await ws.recv())

        # receive the set
        set_obj = deserialize(await(ws.recv()))

        # receive the serialized game object
        game_obj = deserialize(await(ws.recv()))

        # construct the instance
        self.instance = GameInstance(set_obj, assets=self.assets, player_index=self.index)
        self.instance.game = game_obj

    # listens for events from the server, handles accordingly
    async def run(self, host : str = 'localhost', port : int = 8888):
        async with websockets.connect(f"ws://{host}:{port}") as ws:
            await self.establish(ws)


            
        

