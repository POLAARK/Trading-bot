from pickle import TRUE
from pandas import *
import pandas as pd
import yfinance as yf
import requests as rq
from binance import *
import json
from matplotlib import *
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from math import *
from decimal import *
import requests
import os as os

getcontext().prec = 6

class backtest:
    """
    Ce fichier et le fichier pour automatiser le backtest. Il est présent pour la lisibilité du code principal, pour faciliter les changements
    de conditions en fonction des différentes stratégies à tester
    Les fichiers bottrading1 et 2 était initialement des manières de backtester sans instancier des objets backteste à chaque fois
    Néanmoins il était difficile de lire le code, de suivre ce qu'il se passait, de faire des testes unitaires et de changer les conditons 
    des différents backtests 

    Ici pour chaque trade on créé un objet backtest avec différents paramètres. 

    """
    def __init__(self,dataframe5, dataframe1, filename : str, TP : float, SL : float, \
         indice : int, end : int, enCours : bool, Capital : float, nombreDeTrade : int, Winrate, Gainmoyentrade : float, Lindex = [],\
            Lprice = [], LCapital = []):
        #On instancie les différentes données nécéssaires au trade
        self.dataframe5 = dataframe5    #Dataframe sur laquelle on cherche des entrées 
        self.dataframe1 = dataframe1    #Dataframe la plus petite possible ou l'on cherche des sorties (1 minute)
        self.filename = filename    
        self.TP = TP   #Tp du trade courant
        self.SL = SL    #Sl du trade courant 
        self.indice = indice    #Indice d'entrée dans le trade, de parcourt de la dataframe 5 (Celle ou l'on cherche des entrées)
        self.end = end  #L'indice maximum de la base de donée
        self.enCours = enCours  #Si le trade est en cours ou pas
        self.Capital = Capital  #Capital à l'entrée du trade
        self.nombreDeTrade = nombreDeTrade  #Nombre de trade à l'entrée du trade
        self.Winrate = Winrate  #Le winrate à l'entrée du trade
        self.Gainmoyentrade = Gainmoyentrade    #Le gain moyen à l'entrée du trade
        self.Lindex = Lindex    #L'indice d'entrée dans le trade de la PETITE dataframe (donc dataframe1)
        self.Lprice = Lprice    #Le prix de l'asset à l'entrée du trade
        self.LCapital = LCapital    #Le Capital à l'entrée du trade

    def updateL(self, Capital, indice, price):
        # A chaque itération faut update chaucune des variables suivantes: Capital index et prix
        self.LCapital.append(Capital)   
        self.Lindex.append(indice)
        self.Lprice.append(price)


    
    def automatisation_backtest(self, TP : float, SL : float, typetrade : str, entrycondition : bool, outcondition,\
        indice : int, enCours : bool, timeframe : str, Lindex = [], Lprice = [], LCapital = [], monitored = True):
        """
        ---
        Introduction
        ---
        Cette fonction est celle du backtest, pour chaque trade on va vérifier à chaque étape si : 
        -On atteint un prix de sortie (TP ou SL) dans le cas d'un trade monitored 
        -On atteint une des conditions de sorties sur les indicateurs
        ---
        Paramètres
        ---
        Tp : prix de sortie positif du trade (pour prendre des profits)
        Sl : Prix de sortie négatif du trade (pour limiter les pertes)
        typetrade : Le type de trade, short ou long
        entrycondition  

        """
        self.outcondition = outcondition
        self.TP = TP
        self.SL = SL
        self.indice = indice
        self.enCours = enCours
        Entryprice = 1
        Outprice = 1
        looping_times = self.get_times_to_loop(timeframe)
        if typetrade == 'long':
            Entryprice = self.dataframe5.loc[int(self.indice),'price']
            entryTimestamp = self.dataframe5.loc[int(self.indice),'date']
            entryTime = datetime.utcfromtimestamp(entryTimestamp + 7200).strftime('%Y-%m-%d %H:%M:%S')

            #on initialise les datas pour la timeframe 1m
            
            index = self.dataframe1.index[self.dataframe1['date'] == entryTimestamp+self.getcurrentindex(timeframe)].tolist()[0]
           
            """" Exemples de tests unitaires qui ont pu etre effectués, on vérifie que la dataframe 1m est bien synchronisé avec la dataframe de base"""
            # print(Entryprice) 
            # print(self.dataframe1.loc[index,'price'])

            while self.enCours: #or (self.dataframe5.loc[int(self.indice),'PSARdir'] == 'bull') and self.indice < self.end
                #ici on passe sur la dataframe une minute
                #Les données en commun sont la date et l'heure de la mesure donc on va récupérer ca
                
                index +=1
                
                
                if index % looping_times == 0:
                    self.indice += 1
                    #Lorsque l'indice est un chiffre rond c'est que nous sommes à la cloture d'une bougie correspondant à la time frame
                    #Choisie initiale donc on l'ajoute à la liste pour pouvoir tracer le graphique à la fin
                    date = datetime.utcfromtimestamp(self.dataframe5.loc[self.indice,'date']).strftime('%Y-%m-%d %H:%M:%S')
                    self.updateL(self.Capital, date, self.dataframe5.loc[self.indice,'price'])
                #Conditions de sorties TP et SL si le trade est monitored
                if monitored:
                    if (self.dataframe1.loc[index,'price'] - Entryprice)/Entryprice > self.TP:
                        self.enCours = False
                        break
                    if (Entryprice -self.dataframe1.loc[index,'price'])/Entryprice > self.SL:
                        self.enCours = False
                        break

            #Lorsque le code qui est ici se lance c'est que le trade est cloturé, on lance mets à jours alors toutes les variables relatives à un trade
            outTime = datetime.utcfromtimestamp(self.dataframe1.loc[index,'date'] + 7200).strftime('%Y-%m-%d %H:%M:%S')
            Outprice = self.dataframe1.loc[index,'price']
            Resultattrade = self.Capital * (Outprice - Entryprice)/Entryprice
            if Resultattrade >= 0:
                self.Winrate +=1
            self.Capital = self.Capital + Resultattrade
            self.nombreDeTrade += 1
            self.Gainmoyentrade += Resultattrade
            #Ici on enregistre le trade qui vient de se terminer ceci est un teste unitaire, il permet la validation d'un trade de plus 
            #Cela permet une verification si les données renvoyées ne sont pas abérantes, si les trades on bien pu etre prix en regardant les
            #différents graphiques
            ClosedTrade = {'Long ou short' : typetrade, 'Entry price' : Entryprice, 'Out price' : Outprice, 'Benefice on trade' : Resultattrade, 'Capital after this trade' : self.Capital, 'Date d\'entree' : entryTime, 'Date de sortie' : outTime}
            self.appendtrade(self.filename, ClosedTrade)
            if not index % looping_times == 0:
                self.indice = ceil(index / looping_times)
                date = datetime.utcfromtimestamp(self.dataframe5.loc[self.indice,'date']).strftime('%Y-%m-%d %H:%M:%S')
                self.updateL(self.Capital, date, self.dataframe5.loc[self.indice,'price'])

        if typetrade == 'short':
            Entryprice = self.dataframe5.loc[int(self.indice),'price']
            entryTimestamp = self.dataframe5.loc[int(self.indice),'date']
            entryTime = datetime.utcfromtimestamp(entryTimestamp + 7200).strftime('%Y-%m-%d %H:%M:%S')
            #on initialise les datas pour la timeframe 1m

            index = self.dataframe1.index[self.dataframe1['date'] == entryTimestamp+self.getcurrentindex(timeframe)].tolist()[0]
            # print(Entryprice) 
            # print(self.dataframe1.loc[index,'price'])
            while self.enCours: #or (self.dataframe5.loc[int(self.indice),'20Zscore_price'] > -2.4 ) and self.indice < self.end
                #ici on passe sur la dataframe une minute
                #Les données en commun sont la date et l'heure de la mesure donc on va récupérer ca
                index +=1
                # print(index, index%looping_times)
                if index % looping_times == 0:
                    self.indice += 1
                    # print("indice 1h ", self.indice)
                    #Lorsque l'indice est un chiffre rond c'est que nous sommes à la cloture d'une bougie correspondant à la time frame
                    #Choisie initiale donc on l'ajoute à la liste pour pouvoir tracer le graphique à la fin
                    
                    date = datetime.utcfromtimestamp(self.dataframe5.loc[self.indice,'date']).strftime('%Y-%m-%d %H:%M:%S')
                    self.updateL(self.Capital, date, self.dataframe5.loc[self.indice,'price'])
                #Conditions de sorties TP et SL si le trade est monitored
                if monitored:
                    if (Entryprice - self.dataframe1.loc[index,'price'])/Entryprice > self.TP:
                        self.enCours = False
                        break
                    if (self.dataframe1.loc[index,'price'] - Entryprice)/Entryprice > self.SL:
                        self.enCours = False
                        break
            #Lorsque le code qui est ici se lance c'est que le trade est cloturé, on lance mets à jours alors toutes les variables relatives à un trade
            outTime = datetime.utcfromtimestamp(self.dataframe1.loc[index,'date'] + 7200).strftime('%Y-%m-%d %H:%M:%S')
            Outprice = self.dataframe1.loc[index,'price']
            Resultattrade = self.Capital * (Entryprice - Outprice)/Entryprice
            if Resultattrade >= 0:
                self.Winrate +=1
            self.Capital = self.Capital + Resultattrade
            self.nombreDeTrade += 1
            self.Gainmoyentrade += Resultattrade

            ####
            #Ici on enregistre le trade qui vient de se terminer ceci est un teste unitaire, il permet la validation d'un trade de plus 
            #Cela permet une verification si les données renvoyées ne sont pas abérantes, si les trades on bien pu etre prix en regardant les
            #différents graphiques

            ClosedTrade = {'Long ou short' : typetrade, 'Entry price' : Entryprice, 'Out price' : Outprice, 'Benefice on trade' : Resultattrade, 'Capital after this trade' : self.Capital, 'Date d\'entree' : entryTime, 'Date de sortie' : outTime}
            self.appendtrade(self.filename, ClosedTrade)
            if not index % looping_times == 0:
                self.indice = ceil(index / looping_times)
                date = datetime.utcfromtimestamp(self.dataframe5.loc[self.indice,'date']).strftime('%Y-%m-%d %H:%M:%S')
                self.updateL(self.Capital, date, self.dataframe5.loc[self.indice,'price'])

    def getcurrentindex(self, timeframe : str):
        """
        En fonction de la timeframe initiale de la data de base on doit décaler l'indice pour que le prix corresponde à celui de la dataframe 
        1 minute 
        Cette fonciton automatise ce travail.
        """
        pas = 0
        if timeframe == '5m':
            pas =  240 #5*60 - 60
        elif timeframe == '15m':
            pas = 15*60 - 60
        elif timeframe == '1h':
            pas = 60 * 60 - 60
        elif timeframe == '2h':
            pas = 120 * 60 - 60
        elif timeframe == '4h':
            pas = 240 * 60 - 60
        elif timeframe == '1d':
            pas = 24 * 60 * 60 - 60
        return pas

    def get_times_to_loop(self, timeframe):
        times = 0
        if timeframe == '5m':
            times =  5
        elif timeframe == '15m':
            times = 15
        elif timeframe == '1h':
            times = 60
        elif timeframe == '2h':
            times = 120
        elif timeframe == '4h':
            times = 240
        elif timeframe == '1d':
            times = 24 * 60
        return times

    def update_k(self):
        return self.indice

    def appendtrade(self, filename : str, ClosedTrade):
        """"
        Cette fonction permet d'entrenir une base donnée qui contient des informations sur chaque trades pris en backtesting
        Ces informations présentent à la fin du backtesting comme une liste de trade dans un .json sous la forme suivante:
        {
            "Long ou short": "short",
            "Entry price": 40352.39,
            "Out price": 40418.34,
            "Benefice on trade": -2.7163609979582475,
            "Capital after this trade": 1659.3254641787703,
            "Date d'entree": "2022-04-13 13:45:00",
            "Date de sortie": "2022-04-13 13:50:00"
        }

        ---
        Paramètres 
        ---
        filename : nom du fichier sous forme string
        ClosedTrade : dernier trade fermé
        """
        if not os.path.isfile(filename):
            #On regarde si le fichier est créer si non on le créer
            with open(filename, 'w') as e:
                json.dump({'trades' :[ClosedTrade]},e, indent = 4)
                
        else : 
            #On regarde si le fichier est vide, si oui alors on créé l'architecture du fichier
            if os.stat(filename).st_size == 0:
                    with open(filename, 'w') as e:
                        json.dump({'trades' :[ClosedTrade]},e, indent = 4)

            #Si le fichier est non vide et est créé alors on peut ajouter chaque trade qui a été fait.
            else :
                with open(filename, 'r+') as e:
                    file = json.load(e)
                    file["trades"].append(ClosedTrade)
                    e.seek(0)
                    json.dump(file, e, indent = 4)