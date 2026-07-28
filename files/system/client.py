# Demetre Seturidze
# Chess
# Client

from netlib.server import Address, SenderClient, Closure
from netlib import logs
from netlib.serialization import serialize, deserialize

from files.system.items import Request, Response, EngineResponse, EngineRequest, EngineError, EngineEvent, Text, Error, Challenge, Layout, SystemRequest
from files.system.ui import to_UI, UIType

import time 

from applib.controls import FocusContainer, fetch
from applib.utils import Surface
import pygame as pg 

import asyncio

class NetworkClient(SenderClient):
    def __init__(
        self, 
        obj : UIType,
        auth_kwargs : dict = {"glyph_length" : 25},
        middle_kwargs : dict = {"glyphs_per_line" : 36},
        send_interval : float = 0.01
        ):
        self.ui = to_UI(obj)

        self.username = None 

        self.auth_kwargs = auth_kwargs
        self.middle_kwargs = middle_kwargs

        self.auth_interface = None
        self.auth_lock = asyncio.Lock()
        
        self.middle_interface = None
        self.middle_lock = asyncio.Lock()

        self.game_interface = None
        self.game_lock = asyncio.Lock()

        self.current_interface : FocusContainer[SystemRequest] = None 
        self.current_lock = None

        self.sent_challenges = {}
        self.challenge_lock = asyncio.Lock()

        self.window : pg.Window | None = None 
        self.screen : Surface | None = None

        self.lock = asyncio.Lock()

        super().__init__(send_interval=send_interval)


    def _switch_interface(self, next_interface, next_lock):
        if next_interface is not self.current_interface:
            if self.current_interface is self.game_interface:
                self.game_interface = None 

            
            self.current_interface = next_interface
            self.current_lock = next_lock

            topleft = self.window.position

            anchor_y = topleft[1]
            anchor_x = topleft[0] - self.current_interface.width // 2 + self.window.size[0]//2

            self.window.size = self.current_interface.shape
            self.window.position = (anchor_x, anchor_y)

            self.screen = self.window.get_surface()


    # establishes connection and returns a wrapped connection object
    # does NOT add the client to the set of connections. that is done by the handler loop.
    # requires self.lock to alter attributes
    async def establish(self, ws):
        welcome = None 

        self.auth_interface = self.ui.AuthInterface(**self.auth_kwargs)
        
        self.current_interface = self.auth_interface
        self.current_lock = self.auth_lock

        self.window = pg.Window(title="OBCHESSED", size=self.auth_interface.shape)
        self.window.set_icon(self.ui.icon)
        self.window.focus()
        self.screen = self.window.get_surface()

        asyncio.create_task(self.ui_loop())
        
        message = await ws.recv()
        print(message)

        while welcome is None:
            while True:
                await asyncio.sleep(0.5)
                async with self.send_lock:
                    if self.send_buffer:
                        await ws.send(serialize(self.send_buffer[0]))
                        self.send_buffer.pop(0)
                        break

            message = await ws.recv()
            msg = deserialize(message)

            if isinstance(msg, Error):
                self.current_interface.show_message(msg)
            elif isinstance(msg, Response):
                if msg.label == 'welcome':
                    welcome = msg.content
                else:
                    self.current_interface.show_message(msg)
            else:
                logs.error(self, message)

        async with self.middle_lock:
            self.middle_interface = self.ui.MiddleInterface(welcome['u'], **self.middle_kwargs)
            self.username = welcome['u']
            for a in welcome['a']:
                self.middle_interface.add(a)

        async with self.lock:
            self._switch_interface(self.middle_interface, self.middle_lock)



    
    async def register(self, message : str):
        msg = deserialize(message)

        if isinstance(msg, Response):
            if msg.label == 'decline':
                async with self.challenge_lock:
                    d = self.sent_challenges.pop(msg.content, None)
                if d is None:
                    await self.queue(Error("invalid", f"misfire: {message}"))
                    logs.error(self, message)
                else:
                    async with self.middle_lock:
                        self.middle_interface.show_message(msg)
            elif msg.label == 'add':
                async with self.middle_lock:
                    if self.middle_interface is not None:
                        self.middle_interface.add(msg.content)
            elif msg.label == 'delete':
                async with self.middle_lock:
                    if self.middle_interface is not None:
                        self.middle_interface.delete(msg.content)

        elif isinstance(msg, Error):
            async with self.lock:
                async with self.current_lock:
                    self.current_interface.show_message(msg)

        elif isinstance(msg, (EngineResponse, EngineEvent, Text)):
            async with self.game_lock:
                if self.game_interface is None:
                    await self.queue(Error("invalid", f"misfire: {message}"))
                    logs.error(self, message)
                else:
                    self.game_interface.register(msg)

        elif isinstance(msg, EngineError):
            if msg.label == 'InGame':
                async with self.game_lock:
                    self.game_interface.register(msg)
            else:
                async with self.lock:
                    async with self.current_lock:
                        self.current_interface.show_message(msg)

        elif isinstance(msg, Layout):
            async with self.game_lock:
                if self.game_interface is None:
                    board = deserialize(msg.board_str)
                    player_index = msg.players.index(self.username)

                    self.game_interface = self.ui.GameInterface(board, player_index)
                else:
                    #TODO: some other cases here -- what if it's for a different game? but that's for later. one step at a time.
                    self.game_interface.register(msg)

            async with self.lock:
                self._switch_interface(self.game_interface, self.game_lock)

        elif isinstance(msg, Challenge):
            if msg.receiver == self.username:
                async with self.middle_lock:
                    self.middle_interface.show_challenge(msg)
            else:
                await self.queue(Error("invalid", f"misfire: {message}"))
                logs.error(self, message)

        else:
            await self.queue(Error("invalid", f"misfire: {message}"))
            logs.error(self, message)

    async def send(self, message, ws):
        await super().send(message, ws)

        if isinstance(message, Request):
            if message.label == 'close':
                async with self.lock:
                    if self.current_interface is self.game_interface:
                        self._switch_interface(self.middle_interface, self.middle_lock)
            elif message.label == 'quit':
                await ws.close()
                await ws.recv()




    #TODO: UI LOOP IS DEPLOYED IN A FRAGILE MANNER
    # CONSIDER DOING THIS DIFFERENTLY
    async def ui_loop(self, time_refresh : float = 0.5):
        # keeps track of loop parameters to be able to modularize the event loop.
        # this thing gets passed around and edited in-place as opposed to holding
        # all variables locally inside the run function
        last_time = time.time()

        while True:
            events = fetch()
            if events:
                async with self.lock:
                    async with self.current_lock:
                        results = self.current_interface.process(events)
                        if self.screen is not None:
                            self.current_interface.blit_onto(self.screen)
                            self.window.flip()

                        if self.current_interface is self.game_interface:
                            now_time = time.time()
                            if now_time-last_time > time_refresh:
                                results.append(
                                    EngineRequest.construct("times")
                                )
                                last_time = now_time

                if results:
                    print(results)
                    await self.queue_iter(results)
            await asyncio.sleep(0)
    

    async def run(self, address = Address(), loops = None, reconnection_interval = None, **kwargs):
        return await asyncio.gather(
            super().run(address, loops, reconnection_interval, **kwargs),
        )
    