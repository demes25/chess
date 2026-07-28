# Demetre Seturidze
# Chess
# Server

from netlib.server import Server
from netlib.graph import Graph

import asyncio, websockets
from pathlib import Path 

from netlib.serialization import serialize, deserialize
from netlib import logs

from files.system.items import User, Relation, Text, Request, Response, Error, Auth, Challenge
from files.engine import EngineRequest


class Network(Graph[User, Relation]):
    def __init__(self, users : dict[str, User] | None = None, relations : dict[str, dict[str, Relation]] | None = None):
        super().__init__(NodeType='User', EdgeType='Relation', nodes=users, edges=relations)

    async def login(self, username : str, password : str) -> User:
        async with self.lock:
            user = self.nodes.get(username, None)

        if user is None:
            raise LookupError("No such user found.")
        else:
            async with user.lock:
                if password != user.password:
                    raise PermissionError("Incorrect password.")

        return user

    async def signup(self, username : str, password : str) -> User:
        async with self.lock:
            t = username in self.nodes 

        if t:
            raise LookupError(f"User {username} already exists.")
        else:
            return await self.create_node(username, password)

    async def relate(self, u1 : str, u2 : str) -> Relation:
        try:
            e = await self.get_edge(u1, u2)
        except LookupError:
            e = await self.create_edge(u1, u2)
            async with e.lock:
                n1 = await self.get_node(u1)
                n2 = await self.get_node(u2)

                async with n1.lock:
                    e.connections[n1.idstr] = n1.connection
                async with n2.lock:
                    e.connections[n2.idstr] = n2.connection
        except Exception as err:
            logs.handle(err)

        return e



class NetworkServer(Server):
    class Connection(Server.Connection):
        def __init__(self, socket : websockets.ServerConnection, user : User):
            self.user : User = user
            self.current_edge : Relation | None = None
            self.send_lock = asyncio.Lock()
            self.recv_lock = asyncio.Lock()
            self.lock = asyncio.Lock()
            
            super().__init__(socket)

        async def send(self, msg : str):
            '''Sends the given message.
            
            Parameters
            ----------
                msg : str 
                    The message string to send.'''
            async with self.send_lock:
                await self.socket.send(msg)
        
        async def recv(self) -> str:
            '''Receives a message.
            
            Returns
            -------
                The received message, as a string.'''
            async with self.recv_lock:
                return await self.socket.recv()
        

    def __init__(self, filepath : Path | None = None):
        if filepath is None:
            self.network = Network()
        else:
            with open(filepath, 'r') as f:
                recstr = f.read()

            self.network = deserialize(recstr)

        

        # all the users that are currently viewing the middle interface
        self.active_users : list[User] = []

        self.current_challenges : dict[int, Challenge] = {}
        
        super().__init__(structure=dict)


    async def _add(self, connection : Connection):
        msg = serialize(
            Response(
                "add",
                connection.user.to_layout()
            )
        )

        async with self.lock:
            self.clients[connection.user.idstr] = connection

            for user in self.active_users:
                if user.connection is not connection:
                    await user.connection.send(msg)

            self.active_users.append(connection.user)
            
    async def _remove(self, connection : Connection):
        msg = serialize(
            Response(
                "delete",
                connection.user.to_layout()
            )
        )

        async with self.lock:
            self.clients.pop(connection.user.idstr)

            if connection.user in self.active_users:
                self.active_users.remove(connection.user)

            for user in self.active_users:
                await user.connection.send(msg)


    def _iter(self):
        yield from self.clients.values()

    async def save(self, filepath : Path):
        async with self.network.lock:
            recstr = serialize(self.network)

        with open(filepath, 'w') as f:
            f.write(recstr)


    # establishes connection and returns a wrapped connection object
    # does NOT add the client to the set of connections. that is done by the handler loop.
    # requires self.lock to alter attributes
    async def establish(self, ws : websockets.ServerConnection) -> Connection:
        '''Conducts the necessary boilerplate associated with registering a new connection.
        
        Parameters
        ----------
            ws : websockets.ServerConnection
                The server connection to register.
        
        Returns
        -------
            A Connection object that wraps the given server connection.
        '''

        user = None 

        await ws.send(
            serialize(
                Response(
                    "auth",
                    "authentication required"
                )
            )
        )

        while user is None:
            auth = await ws.recv()
            auth = deserialize(auth)

            if isinstance(auth, Request) and auth.label == 'quit':
                await ws.close()
                await ws.recv()
            
            elif not isinstance(auth, Auth):
                await ws.send(
                    serialize(
                        Error(
                            "auth",
                            "authentication required"
                        )
                    )
                )

                continue

            if auth.is_new:
                try:
                    user = await self.network.signup(auth.username, auth.password)
                except:
                    await ws.send(
                        serialize(
                            Error(
                                "auth",
                                "username taken"
                            )
                        )
                    )

                    continue
            else:
                try:
                    user = await self.network.login(auth.username, auth.password)
                except Exception as e:
                    if isinstance(e, PermissionError):
                        await ws.send(
                            serialize(
                                Error(
                                    "auth",
                                    "incorrect password"
                                )
                            )
                        )
                    else:
                        await ws.send(
                            serialize(
                                Error(
                                    "auth",
                                    "no such user found"
                                )
                            )
                        )

                    continue
        
        async with user.lock:
            connection = NetworkServer.Connection(ws, user)
            user.connection = connection

            for edge in user.edges.values():
                async with edge.lock:
                    edge.connections[user.idstr] = connection

        active_list = []

        async with self.lock:
            for k in self.active_users:
                active_list.append(k.to_layout())

        await connection.send(
            serialize(
                Response(
                    "welcome",
                    {
                        'u' : user.idstr,
                        'a' : active_list
                    }
                )
            )
        )

        return connection



        
    
    # disconnects the given client connection
    # does NOT remove from the client set. that is done by the handler loop
    # requires self.lock to alter attributes
    async def disconnect(self, connection : Connection):
        '''Conducts the necessary boilerplate associated with removing an existing connection.
        
        Parameters
        ----------
            connection : Server.Connection
                The Connection object to remove.
        '''

        user = connection.user

        async with user.lock:
            user.connection = None

            for edge in user.edges.values():
                async with edge.lock:
                    edge.connections[user.idstr] = None



    # registers the given message
    # returns True if we keep going, False if we quit. 
    # requires self.lock to alter attributes
    async def register(self, message : str, connection : Connection) -> bool:

        msg = deserialize(message)
        edge = connection.current_edge

        response = None
        result = True      

        active = edge is not None and edge.current_session is not None   
        
        if isinstance(msg, Request):
            if msg.label == 'quit':
                await connection.close()
                result = False 
            
            elif msg.label == 'close':
                if connection.current_edge is not None:
                    connection.current_edge = None

            elif msg.label == 'accept':
                game_id = msg.content
                challenge : Challenge | None = self.current_challenges.pop(game_id, None)

                if challenge is None:
                    response = Error("accept", "no such challenge found")
                else:
                    async with connection.lock:
                        connection.current_edge = await self.network.relate(challenge.sender, challenge.receiver)
                        connection.current_edge.make(challenge.game_set, challenge.timer)

                        session = connection.current_edge.current_session
                        response = session.begin()

                        response.game_id = game_id

                    await connection.current_edge.send_to_both(serialize(response))
                    return result 
            elif msg.label == 'decline':
                game_id = msg.content
                challenge : Challenge | None = self.current_challenges.pop(game_id, None)

                if challenge is None:
                    response = Error('decline', 'no such challenge found')
                else:
                    sender_connection = self.network.nodes[challenge.sender].connection
                    await sender_connection.send(serialize(Response('decline', game_id)))
                    return result 
            elif msg.label == 'reset':
                if active:
                    response = edge.current_session.process(msg)
                else:
                    response = Error("reset", "no active session.")
            

        elif isinstance(msg, Challenge):
            async with self.lock:
                self.current_challenges[msg.game_id] = msg 

            receiver = self.network.nodes[msg.receiver]
            if receiver.connection is None:
                response = Error(
                    'challenge',
                    'receiving user inactive'
                )
            else:
                connection.current_edge = await self.network.relate(connection.user.idstr, receiver.idstr)
                await connection.current_edge.send_to_both(message)
                return result 
            
        elif isinstance(msg, (EngineRequest, Text)):
            if active:
                response = edge.current_session.process(msg)

                await edge.send_to_both(serialize(response))
                return result

            else:
                response = Error("engine", "no active session, cannot access engine.")

        elif isinstance(msg, Error):
            logs.error(self, msg)

        else:
            response = Error("request", "unknown request.")

        if response is not None:
            await connection.send(serialize(response))
        return result 


    

    