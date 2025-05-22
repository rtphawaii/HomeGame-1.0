from channels.generic.websocket import AsyncWebsocketConsumer
import json
import random
from .HomeGame import run_game
import asyncio

class ChatConsumer(AsyncWebsocketConsumer):
    #daphne poker_site.asgi:application
    players = {}  # user_id → self instance
    pending_inputs = {}  # user_id → asyncio.Future
    pending_inputs_all={}
    player_count=None
    game_started = False

    

    async def connect(self):
        #creates an instance of a websocket consumer
        print("WebSocket CONNECTED ✅")
        #extract the user_id from the URL's query string
        self.user_id = self.scope['query_string'].decode('utf-8').split('=')[1].strip()
        #store the websocket connection object in a dictionary keyed by user_id
        ChatConsumer.players[self.user_id] = self
        print("[CONNECT] Using user_id:", self.user_id)
        print("[DEBUG] Stored players:", list(ChatConsumer.players.keys()))
        #add the websocket connection to a group called chat - channel layer lets you broadcast a message
        await self.channel_layer.group_add('chat', self.channel_name)
        #accept the websocket connection
        await self.accept()

        # Only the first connected user sets the player count
        if ChatConsumer.player_count is None and not ChatConsumer.pending_inputs:
            # Offload prompting to a background task so receive() can run
            asyncio.create_task(self.prompt_player_count())

        # Start the game when the required number of players have connected
        if (not ChatConsumer.game_started and ChatConsumer.player_count is not None and len(ChatConsumer.players) == ChatConsumer.player_count):
            ChatConsumer.game_started = True  # Prevent duplicate starts
            asyncio.create_task(run_game(list(ChatConsumer.players.keys()), self))
            print("🏁 run_game started")
            await self.broadcast_system(f"🎮 Game started 🎮 - Player Count: {len(ChatConsumer.players)}")

        # # start game 4 player mode
        # if len(ChatConsumer.players) == 4:  # You can change this number
        #     asyncio.create_task(run_game(list(ChatConsumer.players.keys()), self))
        #     print("🏁 run_game finished")
        #     await self.broadcast_system(f"🎮 Game started 🎮 - Player Count: {len(ChatConsumer.players)} ")

    async def prompt_player_count(self):
        while True:
            try:
                input_value = await self.get_input(self.user_id, '🎲 Enter number of players:')
                ChatConsumer.player_count = int(input_value)

                if ChatConsumer.player_count==1:
                    ChatConsumer.player_count=None
                    raise ValueError
                
                if ChatConsumer.player_count>22:
                    ChatConsumer.player_count=None
                    raise ValueError

                # Clear futures
                to_clear = list(ChatConsumer.pending_inputs.items())
                for player, future in to_clear:
                    if not future.done():
                        future.set_result('player count done')
                ChatConsumer.pending_inputs.clear()

                await self.broadcast_system(f"🔢 Player count set to {ChatConsumer.player_count}")
                break

            except ValueError:
                await self.send_to_user(self.user_id, '❌ Invalid entry. Please enter an integer.')


    async def disconnect(self, close_code):
        #handles disconnecting for websockets that are opened
        print(f"❌ WebSocket DISCONNECTED for {self.user_id} with code {close_code}")
        await self.channel_layer.group_discard('chat', self.channel_name)
        ChatConsumer.players.pop(self.user_id, None)

    async def receive(self, text_data):
        #debugging statements to ensure receive is being hit
        print(f"[RECEIVE] from {self.user_id}: {text_data}")
        print(f"[PENDING INPUTS] {ChatConsumer.pending_inputs}")

        #ensure that the JSON message can be parsed
        try:
            data = json.loads(text_data)
            msg = data['message']
        except Exception as e:
            print(f"[ERROR] Failed to parse JSON: {e}")
            return
        
        #round continuation loop - awaits a specific response from any websocket
        if 'awaiting all' in self.pending_inputs_all:
            future = ChatConsumer.pending_inputs_all.pop('awaiting all')
            print(f"[FUTURE ALL] Resolving input for awaiting all")
            #complete the future which resumes get_input_all
            future.set_result(msg)
            print('all future completed')
            return

        # Checks to see if the user is in the pending inputs dictionary
        if self.user_id in ChatConsumer.pending_inputs:
            #pop the future that is stored at the user id key
            future = ChatConsumer.pending_inputs.pop(self.user_id)
            print(f"[FUTURE] Resolving input for {self.user_id}")
            #complete the future which resumes get_input
            future.set_result(msg)
            print('future completed')
        else:
            #if the user is not pending a response - send message as a normal group chat message
            await self.channel_layer.group_send(
                'chat',
                {'type': 'chat_message', 'message': f'{self.user_id[:5]}: {msg}'}
            )

    async def chat_message(self, event):
        #sends a chat message to the entire group of websockets
        await self.send(text_data=json.dumps({'message': event['message']}))

    async def broadcast_system(self, msg):
        #sends a broadcast message to all users for game rules and notifications
        for player in ChatConsumer.players.values():
            await player.send(text_data=json.dumps({'message': f'[SYSTEM]: {msg}'}))
    
    async def send_to_user(self, user_id, message):
        #debug print statement to ensure the send_to_user is being hit
        print('message sent to single user')
        #player is an instance of websocket consumer - specifically subclass ChatConsumer
        #it contains websocket methods defined in consumers
        player = ChatConsumer.players.get(user_id)
        if player:
            #sends a string to one websocket connection - private message
            await player.send(text_data=json.dumps({'message': message}))
    
    async def send_player_info(self, user_id, message):
        #debug print statement to ensure the send_to_user is being hit
        print('player info delivered to client')
        #player is an instance of websocket consumer - specifically subclass ChatConsumer
        #it contains websocket methods defined in consumers
        player = ChatConsumer.players.get(user_id)
        if player:
            #sends a string to one websocket connection - private message
            await player.send(text_data=json.dumps(message))


    async def send_info_all(self, message):
        print('sending info to all players')
        for user_id, player in ChatConsumer.players.items():
            await player.send(text_data=json.dumps(message))


    async def get_input(self, user_id, prompt):
        #send prompt to a specific user over websocket
        await self.send_to_user(user_id, prompt)
        #creates a new future object 
        future = asyncio.Future()
        print(f"[INPUT] Waiting for response from {user_id}")
        #store the future in the pending_inputs dictionary keyed by the user id
        #the user id owes an answer
        ChatConsumer.pending_inputs[user_id] = future
        print('future stored')
        #pauses until the user replies and the future is complete
        #when a user sends a message back the code resumes and returns their response
        response = await future
        print('future delivered to HomeGame bets')
        return response
    
    async def get_input_all(self, prompt):
        #send prompt to all users over websocket
        await self.broadcast_system(prompt)
        #creates a new future object 
        future = asyncio.Future()
        print(f"[INPUT ALL] Waiting for response from any player")
        #store the future in the pending_inputs dictionary keyed by the phrase 'awaiting all'
        #the users owe an answer
        ChatConsumer.pending_inputs_all['awaiting all'] = future
        print('all future stored')
        #pauses until any user replies and the future is complete
        #when a user sends a message back the code resumes and returns their response
        response = await future
        print('all future delivered for game and round start')
        return response

