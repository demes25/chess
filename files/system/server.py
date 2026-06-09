# Demetre Seturidze
# Chess
# Server

import asyncio, json
from typing import Set, Callable, Any, Optional, Awaitable
from files.system.utils import LogUtils as lu, logging

MessageType = str | Callable[[], str] | dict | Callable[[], dict]

# if input is not function, returns.
# if input is argless function, calls it and returns result.
def collapse(foo : Any | Callable[[], Any]) -> Any:
    return foo() if callable(foo) else foo


class Client:
    def __init__(self, 
        reader : asyncio.StreamReader,
        writer : asyncio.StreamWriter,
        system : 'Server',
        handle : Callable[[str], Awaitable[Optional[MessageType]]] | None = None 
    ):
        
        self.reader = reader
        self.writer = writer

        if handle is None:
            async def _handle(line) -> Optional[MessageType]:
                return json.loads(line)
            handle = _handle 

        self.handle = handle

        self.__system__ = system 

        self.lock = asyncio.Lock()
        self.delimit = system.delimit

    async def display(self, msg : MessageType):
        self.writer.write(self.__system__.render(msg))
        await self.writer.drain()

    async def listen(self):
        while True:
            try:
                line = await self.reader.readuntil(self.delimit.encode())
            except asyncio.IncompleteReadError as e:
                # Stream closed before we got the delimiter
                if e.partial:
                    line = e.partial
                else:
                    break
            except EOFError:
                break
            except Exception as e:
                await self.display(lu.handle_dict(e))

            if not line:
                break

            try:
                line = line.decode().strip().strip(self.delimit).strip()
                msg = await self.handle(line)
                
                if msg is None:
                    break 
                else:
                    await self.display(msg)
                
            except Exception as e:
                await self.display(lu.handle_dict(e))
            
class Server:
    # THE FORMAT is:
    # {
    #   'type' : ['status', 'signal', etc...],
    #   'msg' : [MessageType] 
    # }

    def __init__(self, 
                    open_msg : MessageType = {
                        'type' : 'status',
                        'msg' : 'connected'
                    }, 
                    close_msg : MessageType = {
                        'type' : 'status',
                        'msg' : 'disconnected'
                    },

                    delimit : str = ';',  # the line delimiter
                    indent : int = 2 # indent for json formatting
                ):
        
        self.delimit = delimit
        self.indent = indent
        
        self.lock = asyncio.Lock()
        self.clients : Set[Client] = set()
        
        # keeps track of the serve task
        self.serve_task = None 

        self.open_msg = open_msg
        self.close_msg = close_msg
        
        self.server = None 

   
    def to_str(self, msg : MessageType) -> str:
        called = collapse(msg)
        if isinstance(called, str):
            return called
        elif isinstance(called, dict):
            return json.dumps(called, indent=self.indent)
        else:
            raise TypeError(f'expected message of type {str} or {dict}, not {type(called)}')
    
    
    # checks connections continuously if limit is set
    # for now this is only for KILL-SWITCH purposes, for security
    # TODO: enforce security better
    async def limit_strict(self, limit=1, period=1):
        while True:
            await asyncio.sleep(period)
            
            async with self.lock:
                # kill-switch
                kill = len(self.clients) > limit
            
            if kill:
                print({'type' : 'panic', 'msg' : 'connection limit surpassed, shutting down'})
                await self.close_host()
                break

        self.serve_task.cancel()


    def render(self, msg : MessageType, delimit : bool=True) -> bytes:
        str_msg = self.to_str(msg)
        if delimit:
            str_msg = str_msg + self.delimit
        return (str_msg + '\n').encode()
    

    async def handle_client(self, reader : asyncio.StreamReader, writer : asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        logging.info(f'[Server] Client connected: {addr}' )

        async with self.lock:
            client = Client(reader, writer, self)
            self.clients.add(client)
            await client.display(self.open_msg)
            
        try:
            await client.listen()
                
        finally:  
            await client.display(self.close_msg)
            
            async with self.lock:
                self.clients.discard(client)
            client.writer.close()
            await client.writer.wait_closed()

            logging.info(f'[Server] Client disconnected: {addr}')

    
    async def broadcast(self, msg : MessageType):
        rendered_msg = self.render(msg)

        async with self.lock: 
            to_remove = [client for client in self.clients if client.is_closing()]
            for client in to_remove:
                self.clients.discard(client)
            client_list = self.clients.copy()

        for client in client_list:
            try:
                client.writer.write(rendered_msg)
                await client.writer.drain()
            except Exception as e:
                lu.handle(e, "Discarding failed client.")
                async with self.lock:
                    self.clients.discard(client)
    

    async def close_host(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logging.info("[Server] Server closed")

        if self.clients:
            for client in list(self.clients):
                try:
                    await client.display(self.close_msg)
                except:
                    pass
                finally:
                    client.writer.close()
                    await client.writer.wait_closed()

            self.clients.clear()
            logging.info("[Server] Clients disconnected")
        
    async def open_host(self, host = 'localhost', port = 8888):
        await self.close_host()

        self.server = await asyncio.start_server(
            self.handle_client,
            host=host,
            port=port
        )

        logging.info("[Server] Server opened")


    async def serve(self, limit: int = 0): # 0 is no limit...
        
        task = asyncio.create_task(self.server.serve_forever())
        self.serve_task = task 

        if limit > 0:
            task = asyncio.gather(task, self.limit_strict(limit=limit))
            
        try:
            await task
        except asyncio.CancelledError as e:
            pass
            
    async def open_serve(self, host='localhost', port=8888, limit=0):
        await self.open_host(host=host, port=port)
        await self.serve(limit=limit)
        

