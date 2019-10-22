import tweepy
import logger
import time
import sqlite3
import random
import os
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from config import *

'''tweet = api.update_status(f"La batalla ha comenzado:\nElige {carrera1} o {carrera2} con los hastaghs\n\n#Gana{carrera1.capitalize()}\n\n#Gana{carrera2.capitalize()}")

tweet_id = 1184865769622048769'''

def singleton(class_):
    instances = {}
    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance

@singleton
class SingletonDB():

    def __init__(self):
        self.conn = sqlite3.connect('uvaWarBot_twitter.db')
        #self.conn.set_trace_callback(print)
        self.cursor = self.conn.cursor()

    def getConquers(self):
        self.cursor.execute("select distinct conquista from carreras")
        res = self.cursor.fetchall()
        res = [i[0] for i in res]
        return res

    def getVictims(self, conquer):
        self.cursor.execute("SELECT nombre from carreras where nombre!=(?) and conquista!=(?)", (conquer, conquer))
        res = self.cursor.fetchall()
        res = [i[0] for i in res]
        return res

    def isConquer(self, carrera):
        self.cursor.execute("SELECT conquista from carreras where nombre=(?)", (carrera))
        conq = self.cursor.fetchone()
        return carrera == conq[0]

    def getCountKills(self, carrera):
        self.cursor.execute("SELECT nombre from carreras where conquista=(?)", (carrera,))
        return len(self.cursor.fetchall())

    def aConquerB(self, a, b):
        print(a,b)
        self.cursor.execute("UPDATE carreras SET conquista=(?) WHERE nombre=(?) or conquista=(?)",(a,b,b))
        self.conn.commit()

    def store3TweetsId(self, mainTweet, c1, c2,carrera1,carrera2):
        self.cursor.execute("INSERT INTO tweets(mainTweet, tweetc1, tweetc2, carrera1, carrera2) values(?,?,?,?,?)", (mainTweet, c1, c2, carrera1,carrera2))
        self.conn.commit()
    
    def getListaTabla(self):
        self.cursor.execute("select nombre, conquista from carreras")
        res = self.cursor.fetchall()
        return res
    
    def getLastTweetsId(self):
        self.cursor.execute("select * from tweets where mainTweet=(select max(mainTweet) from tweets);")
        res = self.cursor.fetchone()
        return res

class Game():

    def __init__(self):
        self.db = SingletonDB()
        self.seguir = True
        self.tw = Twitter()

    def nextStep(self):
        self.c1, self.c2 = self.getCandidatos()
        self.tw.sendTweets(self.c1,self.c2)

    def resolveConflict(self):

        c1votos, c2votos, self.c1, self.c2 = self.tw.getVotesFromLastWar()
        print (c1votos, self.c1, c2votos, self.c2)
        if(c1votos > c2votos):
            conquer = self.c1
            victim  = self.c2
        elif(c2votos > c1votos):
            conquer = self.c2
            victim  = self.c1
        else:
            conquer = random.choice((self.c1, self.c2))
            victim  = self.c1 if conquer == self.c2 else self.c2

        self.db.aConquerB(conquer, victim)
        self.tw.anunciaVictoria(conquer, victim, [c2votos,c1votos])

        if self.isWinner(conquer):
            self.win(conquer)

        
        
    def isWinner(self, conquer):
        return self.db.getCountKills(conquer) == 52

    def hasNextStep(self):
        return self.seguir

    def win(self, ganador):
        self.seguir = False
        self.tw.anunciaFinYGanador(ganador)
        print("ganador")
        

    def getCandidatos(self):
        candidatos_conq = self.db.getConquers()
        candidato1 = random.choice(candidatos_conq)
        candidato2  = random.choice(self.db.getVictims(candidato1))
        
        return candidato1, candidato2

class Twitter():
    def __init__(self,):
        self.user_name = "@uvawar"
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(API_KEY,API_SECRET)
        self.api = tweepy.API(auth)
        self.db = SingletonDB()

    def sendTweets(self,carrera1,carrera2):
        tweet = self.api.update_status(f"La batalla ha comenzado:\nElige {carrera1} o {carrera2} dando like a uno de los tweets que hay en las respuestas de este tweet.\nEl que tenga más likes dentro de 24h será el ganador.")
        #almacenar el id y las carreras en la BD de alguna manera?¿
        tweet_c1 = self.api.update_status(f"Like a este tweet para luchar en el bando de {carrera1}", in_reply_to_status_id=tweet.id,filename=self.getFoto(carrera1))
        tweet_c2 = self.api.update_status(f"Like a este tweet para luchar en el bando de {carrera2}", in_reply_to_status_id=tweet.id,filename=self.getFoto(carrera2))

        self.db.store3TweetsId(tweet.id, tweet_c1.id, tweet_c2.id, carrera1, carrera2)

    def listaVivos(self,imagen):
        self.api.update_with_media(status=f"Este es el estado actual, con cada carrera y su numero de territorios conquistados",filename=imagen)

    def getFoto(self,carrera):
        if os.path.exists(f"imagenes/{carrera}.jpg"):
            return f"imagenes/{carrera}.jpg"
        else:
            filename = "lista.jpg"
            W, H = (300,200)
            img = Image.new('RGB', (W,H), color = "white")
            draw = ImageDraw.Draw(img)

            if len(carrera)<=4 : carrera = carrera.upper()
            
            font = ImageFont.truetype("fuente.ttf", 82)
            w,h = font.getsize(carrera)

            draw.text(((W-w)/2,(H-h)/2),f"{carrera}",fill=(0,0,0,255),font=font)
            img.save(filename)

            return filename

    def getVotesFromLastWar(self):
        print(self.db.getLastTweetsId())
        carrera1, carrera2, self.main_tweet, tweet_c1_id, tweet_c2_id = self.db.getLastTweetsId()
        print(self.main_tweet)
        print(tweet_c1_id)
        print(tweet_c2_id)
        print(carrera1)
        print(carrera2)

        tweet_c1 = self.api.get_status(tweet_c1_id)
        tweet_c2 = self.api.get_status(tweet_c2_id)

        favs_c1  = tweet_c1._json['favorite_count']
        favs_c2  = tweet_c2._json['favorite_count']

        return (favs_c1, favs_c2, carrera1, carrera2)
    
    def anunciaVictoria(self, conquer, victim, votos):
        votos = sorted(votos)
        self.api.update_status(f"Ha ganado la batalla {conquer} con {votos[1]} votos y caen derrotados {victim} con {votos[0]} votos", in_reply_to_status_id=self.main_tweet)
    
    def anunciaFinYGanador(self, ganador):
        self.api.update_status(f"{ganador} se lleva la victoria!!")

    '''
    def getReplies(self,tweet_id,carrera1,carrera2):
        replies = tweepy.Cursor(self.api.search, q='to:{}'.format(self.user_name),
                                since_id=tweet_id, tweet_mode='extended').items()


        votos = {
            carrera1: 0,
            carrera2: 0
        }

        ids = []
        while True:
            try:
                reply = replies.next()
                if not hasattr(reply, 'in_reply_to_status_id_str'):
                    continue
                if reply.in_reply_to_status_id == tweet_id and reply.user.id not in ids:
                    ids.append(reply.user.id)
                    print("reply of tweet: {}".format(reply.full_text))
                    if (f"#Gana{carrera1}".lower()) in reply.full_text.lower():
                        votos[carrera1] = votos[carrera1] + 1

                    elif (f"#Gana{carrera2}".lower()) in reply.full_text.lower():
                        votos[carrera2] = votos[carrera2] + 1

            except tweepy.RateLimitError as e:
                print("Twitter api rate limit reached".format(e))
                time.sleep(60)
                continue

            except tweepy.TweepError as e:
                print("Tweepy error occured:{}".format(e))
                break

            except StopIteration:
                break

            except Exception as e:
                print("Failed while fetching replies {}".format(e))
                break

        return votos
        '''

tw = Twitter()
