from channels.generic.websocket import AsyncWebsocketConsumer
import json
import random
from .HomeGame import run_game
import asyncio

class ChatConsumer(AsyncWebsocketConsumer):
    #daphne poker_site.asgi:application
    players = {}  # user_id → self instance
    pending_inputs = {}  # user_id → asyncio.Future

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

        # Check if enough players to start game
        if len(ChatConsumer.players) == 4:  # You can change this number
            asyncio.create_task(run_game(list(ChatConsumer.players.keys()), self))
            print("🏁 run_game finished")
            await self.broadcast_system(f"🎮 Game started 🎮 - Player Count: {len(ChatConsumer.players)} ")

    async def disconnect(self, close_code):
        print(f"❌ WebSocket DISCONNECTED for {self.user_id} with code {close_code}")
        await self.channel_layer.group_discard('chat', self.channel_name)
        ChatConsumer.players.pop(self.user_id, None)

    async def receive(self, text_data):
        print(f"[RECEIVE] from {self.user_id}: {text_data}")
        print(f"[PENDING INPUTS] {ChatConsumer.pending_inputs}")

        try:
            data = json.loads(text_data)
            msg = data['message']
        except Exception as e:
            print(f"[ERROR] Failed to parse JSON: {e}")
            return


        # If the user is in the pending inputs dictionary
        if self.user_id in ChatConsumer.pending_inputs:
            #pop the future that is stored at the user id key
            future = ChatConsumer.pending_inputs.pop(self.user_id)
            print(f"[FUTURE] Resolving input for {self.user_id}")
            #complete the future which resumes get_input
            future.set_result(msg)
            print('future completed')
        else:
            await self.channel_layer.group_send(
                'chat',
                {'type': 'chat_message', 'message': f'{self.user_id[:5]}: {msg}'}
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({'message': event['message']}))

    async def broadcast_system(self, msg):
        for player in ChatConsumer.players.values():
            await player.send(text_data=json.dumps({'message': f'[SYSTEM]: {msg}'}))
    
    async def send_to_user(self, user_id, message):
        print('message sent to single user')
        #player is an instance of websocket consumer - specifically subclass ChatConsumer
        #it contains websocket methods defined in consumers
        player = ChatConsumer.players.get(user_id)
        if player:
            #sends a string to one websocket connection - private message
            await player.send(text_data=json.dumps({'message': message}))

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
