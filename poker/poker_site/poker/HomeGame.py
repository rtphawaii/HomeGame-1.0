import sys
sys.path.append('../pokerlib')

from argparse import ArgumentParser
from pokerlib import Player, PlayerSeats
from pokerlib import Table
from pokerlib import HandParser as HandParser
from pokerlib.enums import Rank, Suit
import random
import copy

#UPDATES AND FIXES NEEDED:
#must fix all-in scenarios where one player is out of balance
#in an all-in scenario the player without balance is forced to fold if another player bets
#this is not ideal and instead it should skip their action, carve out a side pot, and let the action carry on for other players

class Table():
    def __init__(self,smallblind,bigblind,input,output,send_to_user,send_player_info,send_info_all):
        self.list=[]
        self.order=[]
        self.startingorder=[]
        self.pot=0
        self.smallblind=smallblind
        self.bigblind=bigblind
        self.currentprice=self.bigblind
        self.bet=[]
        self.board=[]
        self.deck=[]
        self.rank=[]
        self.preflop=True
        self.rivercheck=False
        self.gameover=False
        self.round=1
        self.output=output
        self.input=input
        self.send_to_user=send_to_user
        self.send_player_info=send_player_info
        self.send_info_all=send_info_all
    def createdeck(self):
        '''create the deck'''
        self.deck = [(rank, suit) for rank in Rank for suit in Suit]
        self.shuffledeck()
    def shuffledeck(self):
        random.shuffle(self.deck)
    async def addplayer(self,player):
        '''add a player to the game'''
        self.list.append(player)
        await self.send_to_user(player.player_id,f"you are {player}")
    def pickdealer(self):
        '''pick a dealer'''
        self.order=self.list
        random.shuffle(self.order)
        return self.order[0].name
            
    def deal(self):
        '''deal hands'''
        for x in self.list:
            x.hand.append(self.deck.pop())
            x.hand.append(self.deck.pop())
    async def flop(self):
        '''deals flop'''
        print('flop')
        await self.output(f"now dealing the flop...")
        #burn one card
        self.deck.pop()
        #deal 3 cards to the board
        self.board.append(self.deck.pop())
        self.board.append(self.deck.pop())
        self.board.append(self.deck.pop())
        print(self.board)
        rank1, suit1 = self.board[0]
        rank2, suit2 = self.board[1]
        rank3, suit3 = self.board[2]
        await self.output(f"the flop is: {rank1.name} of {suit1.name}, {rank2.name} of {suit2.name}, {rank3.name} of {suit3.name}")

        #send the update to the board
        board_flop=f"{rank1.name} of {suit1.name}, {rank2.name} of {suit2.name}, {rank3.name} of {suit3.name}"
        await self.send_info_all({
                "board": {
                    'board':board_flop
                }})

        
    async def turn(self):
        '''deals turn'''
        print('turn')
        await self.output(f"now dealing the turn...")
        #burn one card
        self.deck.pop()
        #deal 1 card to the board
        self.board.append(self.deck.pop())
        print(self.board)
        rank1, suit1 = self.board[0]
        rank2, suit2 = self.board[1]
        rank3, suit3 = self.board[2]
        rank4, suit4 = self.board[3]
        await self.output(f"the turn is: {rank1.name} of {suit1.name}, {rank2.name} of {suit2.name}, {rank3.name} of {suit3.name}, {rank4.name} of {suit4.name}")

        #send the update to the board
        board_turn=f"{rank1.name} of {suit1.name}, {rank2.name} of {suit2.name}, {rank3.name} of {suit3.name}, {rank4.name} of {suit4.name}"
        await self.send_info_all({
                "board": {
                    'board':board_turn
                }})
        
    async def river(self):
        '''deals river'''
        print('~river')
        await self.output(f"now dealing the river...")
        #burn one card
        self.deck.pop()
        #deal 1 card to the board
        self.board.append(self.deck.pop())
        print(self.board)
        rank1, suit1 = self.board[0]
        rank2, suit2 = self.board[1]
        rank3, suit3 = self.board[2]
        rank4, suit4 = self.board[3]
        rank5, suit5 = self.board[4]
        print(rank5.name,suit5.name)
        await self.output(f"the river is: {rank1.name} of {suit1.name}, {rank2.name} of {suit2.name}, {rank3.name} of {suit3.name}, {rank4.name} of {suit4.name}, {rank5.name} of {suit5.name}")

        #send the update to the board
        board_river=f"{rank1.name} of {suit1.name}, {rank2.name} of {suit2.name}, {rank3.name} of {suit3.name}, {rank4.name} of {suit4.name}, {rank5.name} of {suit5.name}"
        await self.send_info_all({
                "board": {
                    'board':board_river
                }})
    
    async def bets(self):
        '''betting mechanism'''
        print('betting started')
        #start collecting the first round of bets starting from next to the big blind
        raise_offset=1
        #find the big blind index in self.order
        if self.preflop==True:
            #option to straddle (needs building)
            
            #find the player that is big blind
            player_to_find = self.bet[-1][0]
            found_index = None
            for index, player in enumerate(self.order):
                if player == player_to_find:
                    found_index = index
                    #the action starts one player after the big blind if there has not been a straddle
                    found_index+=1
                    #set an endpoint, the betting should end before reaching the end index based on the loop parameters
                    end_index=found_index
                    break
        else:
            #when it is post flop,river, turn, action starts after the dealer and ends on the dealer
            self.bet=[(self.list[-1],0)]
            found_index=1
            end_index=1
        #once the index of the big blind player is found, loop around starting from the person next to them
        if found_index is not None:
            print('found_index is defined')
            #everything should be in a while loop that resets betting if someone raises
            continue_loop = True
            while continue_loop:
                    #continue through the betting process as normal unless someone raises
                    continue_loop=False
                    print('enter first while loop')
                    #betting loop starts
                    print(self.order[found_index:])
                    print(self.order[:end_index])
                    for offset,player in enumerate(self.order[found_index:] + self.order[:end_index]):
                        print('player betting: ', player)
                        #betting ends if everyone has folded except for one player 
                        if len(self.order)<=1:
                            continue_loop=False
                            return
                        #a player needs to place a valid bet that is a fold, call, check, or raise
                        while True:
                            print('second while loop for individual betting enter')
                            playerbet = await player.placebet(self.bet[-1][1])  # Wait for the player to place a bet
                            print('placebet called', player)

                            if playerbet == -1 or playerbet == self.bet[-1][1] or playerbet > self.bet[-1][1]:
                                print('valid bet - loop break and evaluate')
                                await self.output(f'{player} bets {playerbet}')
                                break  # Valid bet, exit the loop
                            else:
                                print("Invalid bet. Please enter another bet.")
                                await self.send_to_user(player.player_id, '❌ Invalid bet. Please enter another bet.')

                        #remove the player from the order if they fold
                        if playerbet==-1:
                            index = self.order.index(player)
                            self.order.pop(index)
                            print('fold by', player)
                            await self.output(f"{player} has folded")
                        #player raises, evaluate bets for everyone again starting from the next player around to the player that raises
                        elif playerbet>self.bet[-1][1]:
                            #add the bet to the betting log
                            self.bet.append((player,playerbet))
                            #the player object that raised and needs to be found
                            player_to_find = self.bet[-1][0]
                            #find the index of the player that raised
                            for index, player in enumerate(self.order):
                                if player == player_to_find:
                                    found_index = index
                                    found_index+=1
                            #end the betting action on the person before the person that is raising 
                            end_index=found_index-1
                            print('raise')
                            raise_offset=0
                            continue_loop=True
                            break  # Break out of the loop to restart (enter the start of the first while loop)
                        else:
                            #if the bet is a call then it is simply added and we move to the next better
                            self.bet.append((player,playerbet))
                            print(f'{player} calls the bet of {playerbet}')
                            await self.output(f'{player} calls the bet of {playerbet}')
    async def evaluate(self):
        '''determine winner and give pot'''
        hands=[]
        if len(self.order)==1:
            self.order[0].balance+=self.pot
            print(f'everyone else folded... {self.order[0].name} wins {self.pot}')
            await self.output(f"everyone else folded... {self.order[0].name} wins {self.pot}")
        else:
            #add each hand to hands
            for x in self.order:
                x.hand=HandParser(x.hand)
                x.hand+=self.board
                hands.append((x,x.hand))
            #evaluate the best hand and player
            max_player = max(hands, key=lambda x: x[1])
            winner_index = hands.index(max_player)
            winners = []  # List to store players with the maximum hand value
            # Iterate through handlist excluding the winner_index
            winners.append(max_player[0])
            #check to see if there are any other winners
            for index, (player, hand) in enumerate(hands):
                if index != winner_index:
                    if hand == max_player[1]:
                        winners.append(player)
            #if there is one winner add the pot to their balance
            if len(winners)==1:
                winners[0].balance+=self.pot
                print(f'{winners[0].name} wins {self.pot}','with',winners[0].hand.handenum)
                await self.output(f"{winners[0].name} wins {self.pot}, with, {str(winners[0].hand.handenum)}")
            #if there is more than one winner split the pot between them
            else:
                for x in winners:
                    print(x, 'wins with:',x.handscore)
                    await self.output(f"{x} wins with: {x.handscore}")
                    x.balance+=self.pot/len(winners)
    async def fold_check(self):
        if len(self.order)==1:
            self.order[0].balance+=self.pot
            print(f'everyone else folded... {self.order[0].name} wins {self.pot}')
            await self.output(f"everyone else folded... {self.order[0].name} wins {self.pot}")
            self.gameover=True
  
        
    def potcalc(self):
        #takes the latest bets from each player unless the player bet then folded
        latest_bets = {}
        for player, bet in reversed(self.bet):
            if player not in latest_bets and bet != -1:
                latest_bets[player] = bet
            elif player not in latest_bets:
                latest_bets[player] = 0
            elif bet != -1:
                continue  # Skip if player already has a non-negative bet
            elif latest_bets[player] != -1:
                latest_bets[player] = 0  # Treat -1 bet as 0 if there's no previous non-negative bet
            #subtract the latest bet for each player from their balance
            player.balance-=latest_bets[player]
        if all(value > 0.2 for value in latest_bets.values()):
            self.pot -= 0.1
        return sum(value for value in latest_bets.values())
    
    async def pot_info_update(self):
        #send pot info
        await self.output(f"the pot is: {self.pot}")
        await self.send_info_all({
                "pot": {
                    'pot':self.pot
                }})
    
    async def player_info_update(self):
        #sends an update to player info
        
        for player in self.order:
            print(f"Sending stats to {player.player_id}:", player.balance)
            rank1, suit1 = player.hand[0]
            rank2, suit2 = player.hand[1]
            rank1str=str(rank1.name)
            suit1str=str(suit1.name)
            rank2str=str(rank2.name)
            suit2str=str(suit2.name)
            hand=[(rank1str,suit1str),(rank2str,suit2str)]
            await self.send_player_info(player.player_id, {
                "player": {
                    "name": player.name,
                    "balance": player.balance,
                    "currentbet": player.currentbet,
                    "handscore": player.handscore,
                    "hand": [(str(r), str(s)) for r, s in hand]
                }
            })
            print(f'info update sent to player {player}')

    async def Round(self,bet=0):
        print('round enter')
        await self.output("Game round begins")
        #creates a future object stored in a dictionary with user_id as key
        #the future is stored until the websocket receives a message from the user
        #once the future is completed it is returned and the string is stored in move
        #move = await self.input(self.list[0].player_id, "What is your move?")
        #move is sent to all players

        #await self.output(f"{self.list[0]} played: {move}")
        #await self.send_to_user(self.list[0].player_id,"test send to user")

        #reset hands
        for x in self.list:
            x.hand=[]
        if self.round==1:
            #pick a dealer
            self.pickdealer()
            print('dealer picked')
            self.startingorder=copy.copy(self.order)
        print(self.order)
        await self.output(f"{self.order[0]} is the dealer - the order is {self.order}")
        #create a new deck
        self.createdeck()
        #shuffle the deck
        self.shuffledeck()
        #deal each player 2 cards 
        self.deal()
        for player in self.order:
            print(player.hand)
            print(type(player.hand[0][0]))
            rank1, suit1 = player.hand[0]
            rank2, suit2 = player.hand[1]
            msg = f"your hand is {rank1.name} of {suit1.name}, {rank2.name} of {suit2.name}"
            await self.send_to_user(player.player_id, msg)

        #sends an update to player info
        await self.player_info_update()
        
        #preflop
        #add small and big blinds to betting log
        self.bet.append((self.order[1],self.smallblind))
        self.bet.append((self.order[2],self.bigblind))
        #add the small and big blind to the pot
        self.pot=self.smallblind+self.bigblind
        await self.bets()
        self.pot=self.potcalc()
        print('pot is: ',self.pot)

        #send pot info
        await self.pot_info_update()


        self.fold_check()
        
        if self.gameover==False:
            #flop
            await self.flop()
            self.preflop=False
            self.bet=[]
            await self.bets()
            print(self.bet)

            #sends an update to player info
            await self.player_info_update()

            self.pot+=self.potcalc()
            print('pot:',self.pot)
            await self.output(f"the pot is: {self.pot}")

            #send pot info
            await self.pot_info_update()

            await self.fold_check()
        if self.gameover==False:
            #turn
            await self.turn()
            self.preflop=False
            self.bet=[]
            await self.bets()

            #sends an update to player info
            await self.player_info_update()

            print(self.bet)
            self.pot+=self.potcalc()
            print('pot:',self.pot)
            await self.output(f"the pot is: {self.pot}")

            #send pot info
            await self.pot_info_update()

            await self.fold_check()
        if self.gameover==False:
            #river
            await self.river()
            self.preflop=False
            self.bet=[]
            await self.bets()
            print(self.bet)

            #sends an update to player info
            await self.player_info_update()

            self.pot+=self.potcalc()
            print('pot:',self.pot)
            await self.output(f"the pot is: {self.pot}")

            #send pot info
            await self.pot_info_update()

            self.rivercheck=True
            await self.fold_check()
            await self.evaluate()
        for x in self.list:
            print(x,'  ','balance:',x.balance)
            await self.output(f"{x} has the balance: {x.balance}")
            print(x, x.hand)
            print(x.hand.cards)
            readable_cards = [f"{rank.name} of {suit.name}" for rank, suit in x.hand.cards]
            print(x.hand.handenum)
            await self.output(f"{x} has a {str(x.hand.handenum)} with the cards {', '.join(readable_cards)}")
        
        #sends an update to player info
        for player in self.list:
            print(f"Sending stats to {player.player_id}:", player.balance)
            await self.send_player_info(player.player_id, {
                "player": {
                    "name": player.name,
                    "balance": player.balance,
                    "currentbet": player.currentbet,
                    "handscore": player.handscore,
                    "hand": ['']
                }
            })
            print(f'info update sent to player {player}')
        
        #reset variables for next round
        self.order=[]
        self.pot=0
        self.currentprice=self.bigblind
        self.bet=[]
        self.board=[]
        self.deck=[]
        self.rank=[]
        self.preflop=True
        self.rivercheck=False

        #reset pot
        await self.pot_info_update()

        #reset board
        await self.send_info_all({
                "board": {
                    'board':'new round'
                }})


        #change order for next round
        self.round+=1
        self.gameover=False
        #need to fix order picking for subsequent rounds
        self.order=self.startingorder[-(self.round-1):]+self.startingorder[:-(self.round-1)]

    # def Round_Test(self,bet=0):
    #     '''execute one round'''
    #     #reset hands
    #     for x in self.list:
    #         x.hand=[]
    #     if self.round==1:
    #         #pick a dealer
    #         self.pickdealer()
    #         self.startingorder=copy.deepcopy(self.order)
    #     #create a new deck
    #     self.createdeck()
    #     #shuffle the deck
    #     self.shuffledeck()
    #     #deal each player 2 cards 
    #     self.deal()
    #     #preflop
    #     #add small and big blinds to betting log
    #     self.bet.append((self.order[1],self.smallblind))
    #     self.bet.append((self.order[2],self.bigblind))
    #     #add the small and big blind to the pot
    #     self.pot=self.smallblind+self.bigblind
    #     print('order:',[x.name for x in self.order])
    #     self.bets()
    #     print(self.bet)
    #     self.pot=self.potcalc()
    #     print('pot:',self.pot)
    #     self.fold_check()
        
    #     if self.gameover==False:
    #         #flop
    #         self.flop()
    #         self.preflop=False
    #         self.bet=[]
    #         self.bets()
    #         print(self.bet)
    #         self.pot+=self.potcalc()
    #         print('pot:',self.pot)
    #         self.fold_check()
    #     if self.gameover==False:
    #         #turn
    #         self.turn()
    #         self.preflop=False
    #         self.bet=[]
    #         self.bets()
    #         print(self.bet)
    #         self.pot+=self.potcalc()
    #         print('pot:',self.pot)
    #         self.fold_check()
    #     if self.gameover==False:
    #         #river
    #         self.river()
    #         self.preflop=False
    #         self.bet=[]
    #         self.bets()
    #         print(self.bet)
    #         self.pot+=self.potcalc()
    #         print('pot:',self.pot)
    #         self.rivercheck=True
    #         self.fold_check()
    #         self.evaluate()
    #     for x in self.list:
    #         print(x,'  ','balance:',x.balance)
    #         print(x, x.hand)
        
    #     #reset variables for next round
    #     self.order=[]
    #     self.pot=0
    #     self.currentprice=self.bigblind
    #     self.bet=[]
    #     self.board=[]
    #     self.deck=[]
    #     self.rank=[]
    #     self.preflop=True
    #     self.rivercheck=False

    #     #change order for next round
    #     self.round+=1
    #     self.gameover=False
    #     self.order=self.startingorder[-(self.round-1):]+self.startingorder[:-(self.round-1)]
        
   
    
        
class Player():
    def __init__(self,player_id,balance,table):
        self.player_id=player_id
        self.balance=balance
        self.hand=[]
        #need to fix currentbet
        self.currentbet=0
        #need to fix handscore
        self.handscore=0
        self.table=table
        self.name=f'player #{self.player_id[:5]}'
    def __repr__(self):
        return (f'{self.name}')
    async def placebet(self, current_price, valid=True):
        print("[DEBUG] Prompting player:", self.player_id)
        '''place a bet'''
        if valid == False:
            while True:
                try:
                    print('placebet enter invalid bet attempted')
                    bet = float(await self.table.input(self.player_id,f"price is {current_price}, Invalid Bet Size, what is your new bet (0 for check, -1 for fold): "))
                    if bet <= self.balance:  # Check if bet is within balance
                        return bet
                    else:
                        await self.table.send_to_user(self.player_id,"Invalid bet. Bet exceeds balance.")
                except ValueError:
                    await self.table.send_to_user(self.player_id,"Invalid input. Please enter a valid number.")
        else:
            while True:
                print('placebet enter')
                try:
                    print('placebet valid input')
                    bet = float(await self.table.input(self.player_id,f'{self.name}, price is {current_price}, place your bet (0 for check, -1 for fold): '))
                    print('placebet valid done')
                    if bet <= self.balance:  # Check if bet is within balance
                        print('bet: ',bet)
                        return bet
                    else:
                        await self.table.send_to_user(self.player_id,"Invalid bet. Bet exceeds balance.")
                except ValueError:
                    await self.table.send_to_user(self.player_id,"Invalid input. Please enter a valid number.")
    
        
async def run_game(player_ids, consumer, smallblind=.10, bigblind=.10):
    #create the table 
    table = Table(smallblind, bigblind, output=consumer.broadcast_system, input=consumer.get_input,send_to_user=consumer.send_to_user,send_player_info=consumer.send_player_info,send_info_all=consumer.send_info_all)
    #add players once 4 people have joined
    for player_id in player_ids:

        player=Player(player_id=player_id,balance=20,table=table)
        await table.addplayer(player)

    #start the first round
    print(f"Starting game with {player_ids}")
    #await table.Round()

    print(f"round end")

    # need to fix round continuation loop
    round_continue = True

    while round_continue:
        round_continue = False
        pending_response=True
        while pending_response:
            round_start=await(consumer.get_input_all('Would You Like To Play Another Round, Enter "start new round": '))
            if round_start=='start new round':
                await table.Round()
                round_continue=True
                pending_response=False
            else:
                await(consumer.broadcast_system('[INVALID ENTRY]'))
    
    #end round continuation loop

    return {
        "status": "started",
        "players": player_ids
    }

         