from pickle import TRUE
from pandas import *
import pandas as pd
import yfinance as yf
import requests as rq
from binance import *
import asyncio
import json
import requests
import time
from matplotlib import *
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from math import *
from decimal import *

api_key = '0W0NnouXJG5kHRuvjm7AcZNOSYxHHPmNWItts8ZUWcIp9aQv4QyCKUa1EbRTE4Iw'
api_secret = 'NmW0ruph3E8qvg5c9c9ngEgukPVkHKCHYBPE27ZB8UBtD7kvI79JiWQDU7SXbwrF'
client = Client(api_key, api_secret)

dataframe6mois5m = pd.read_pickle("./dataframe6mois5mETH.pkl")
dataframe6mois1m = pd.read_pickle("./dataframe6mois1mETH.pkl")

LCapital = [1000]
Lprice = []
Lindex = []
L = []
LTP = []
LSL = []
Lcapital = []

"""
cette fonction optimise les tps et SL pour une stratégie donnée:
Pour ce faire on va lancer un backtesting pour des valeurs de TPs et SLs différentes 
Lorsque toutes les valeurs de TP et SL ont été testé alors on renvoie le couple (TP,SL) donnant les meilleurs résultats

Comment parcourt-t-on les différents TP/SL:
    On cherche un ratio TP/SL >1. Pour cela on parcourt les valeurs de TP avec un pas de 0.0005 (0.005%) modifiable en fonction des stratégies
    et des timeframes
    Ensuite pour une valeure de TP fixée on utiliser toutes les valeurs de SL possible qui satisfasse le ratio
    Dans le code suivant on veut que TP/SL > 10/7. 
    On refait ces opérations jusqu'à avoir parcouru toutes les valeurs possibles de TP

    /!\ Il faut prendre en compte la timeframe 
    En effet si l'on utilise des stratégies intraday (timeframe = 1d) ou meme sur plusieurs jours les TP sont de l'ordre de plusieurs pourcents TP = o(10)
    Donc le pas sera plus élévé que dans l'exemple précédent, de l'ordre de 0.2% = 0.002
"""

async def main(filename,backtest,start,end):
    TP = Decimal('0.01')
    SL = Decimal('0.001')
    Capitaltest = 0
    couple = [TP,SL, Capitaltest]
    file = open(filename, 'w+')
    entryTime = start
    typetrade = 'long'
    nombreDeTrade = 0
    Bornes = 0
    enCours = False
    Capital = 1000
    if backtest == 'True':
        #On va essayer d'optimiser les Tps et SL pour la stratégie:

        while TP < 0.02:
            TP += Decimal('0.0005')
            SL = Decimal('0.001')
            while SL < TP/2 + TP/5:
                SL += Decimal('0.0005')
                Capital = 1000
                Entryprice = 0
                LzScore = [dataframe6mois5m.loc[start,'zscore']]
                LzScoreMA = [dataframe6mois5m.loc[start,'zscoreMA']]

                #Pour simuler le short en gain je vais juste faire prix de sortie-prix d'entrée
                k = Decimal(start)
                while k < end:
                    k+=Decimal(1)

                    if dataframe6mois5m.loc[int(k)-1,'zscore'] >= 2.4 and dataframe6mois5m.loc[int(k),'zscore'] < dataframe6mois5m.loc[int(k) - 1, 'zscore']:
                        Bornes = 1
                    if  dataframe6mois5m.loc[int(k)-1,'zscore'] <= -2.4 and dataframe6mois5m.loc[int(k),'zscore'] > dataframe6mois5m.loc[int(k) - 1, 'zscore']:
                        Bornes = -1
                        
                    #Short condition
                    if Bornes == -1 :
                        typetrade = 'short'
                        # print('entrée dans trade')
                        Bornes = 0 
                        Entryprice = dataframe6mois5m.loc[int(k),'price']
                        entryTimestamp = dataframe6mois5m.loc[int(k),'date']
                        entryTime = datetime.utcfromtimestamp(entryTimestamp).strftime('%Y-%m-%d %H:%M:%S')
                        #on initialise les datas pour la timeframe 1m
                        index = dataframe6mois1m.loc[dataframe6mois1m['date'] == entryTimestamp+240,'price'].index[0]
                        enCours = True
                        # while enCours:
                        while dataframe6mois5m.loc[int(k)-1,'zscore'] < 2.4 and k<end or enCours and k < end:
                            #ici on passe sur la dataframe une minute
                            #Les données en commun sont la date et l'heure de la mesure donc on va récupérer ca
                            
                            index +=1
                            k = Decimal(str(k)) + Decimal('0.2')

                            if (dataframe6mois1m.loc[index,'price']-Entryprice)/Entryprice > TP:
                                enCours = False
                                break
                            if (Entryprice - dataframe6mois1m.loc[index,'price'])/Entryprice > SL:
                                enCours = False
                                break
                            
                        Outprice = dataframe6mois1m.loc[index,'price']
                        Resultattrade = Capital * (Outprice - Entryprice)/Entryprice
                        Capital = Capital + Resultattrade
                        if not Decimal(str(k))%1 == 0.0:
                            k = Decimal(ceil(k))
                LTP.append(float(TP))
                LSL.append(float(SL))
                Lcapital.append(float(Capital))
                L.append([float(TP),float(SL),Capital])
                if Capital > Capitaltest:
                    Capitaltest = Capital 
                    couple = [float(TP), float(SL), Capitaltest]

        fichier = open("data.txt", "w")
        fichier.write(str(L))
        fichier.close()
        print(couple)
        fig = plt.figure(figsize=(0.024,0.024,))
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(xs = LTP, ys = LSL, zs = Lcapital)
        plt.show()


asyncio.run(main('essai.json' ,'True',58000,59000))
# 60960