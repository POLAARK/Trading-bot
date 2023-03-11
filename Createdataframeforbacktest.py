from cProfile import label
from pickle import TRUE
from turtle import back
from attr import NOTHING
from pandas import *
import pandas as pd
import yfinance as yf
import requests as rq
from binance import *
import time as time
from matplotlib import *
import matplotlib.pyplot as plt
import numpy as np
import datetime as datetime
from math import *
from decimal import *
import Indicateursbacktest as ind
import os

#On va faire ça avec l'api binance
#Clefs qui doivent etre passées en privées 

#Pour récupérer des informations a propose de symboles on a besoin des clefs apis binance 
#Ces dernieres sont à insérer ci dessous 
api_key = '0W0NnouXJG5kHRuvjm7AcZNOSYxHHPmNWItts8ZUWcIp9aQv4QyCKUa1EbRTE4Iw'
api_secret = 'NmW0ruph3E8qvg5c9c9ngEgukPVkHKCHYBPE27ZB8UBtD7kvI79JiWQDU7SXbwrF'
client = Client(api_key, api_secret)


def dataframe(filename, timeframe : str, Starttime : int , backtest : bool, pair : str,):
    """
    Fonction qui renvoit la data depuis le temps spécifié.
    Créé une dataframe à partir de différentes données spécifiées

    ---
    Paramètres
    ---

    -La timeframe (1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d)

    -Le temps de début en unix à 10 digit (donc milli secondes)

    -Backtest : True si les données doivent etre sauvegardés pour pouvoir travailler dessus ou False si c'est des données à utiliser en live trading
    
    -La paire avec "pair" : Toutes les paires disponibles sur binance sont récupérables. Par exemple : BTCUSDT renvoie les différents prix du bitcoin en fonction du prix du dollar.

    ---
    Remarques
    ---
    On n'effectue pas de calculs des indicateurs sur la dataframe 1 minutes car, on n'élabore pas de stratégies sur une timeframe aussi faible (trop volatile) et le temps de calcul des indacateurs est
    très long
    """
        
    #Ici choix de la timeframe
    if timeframe == '5m':
        timeframe =  client.KLINE_INTERVAL_5MINUTE
    elif timeframe == '1m':
        timeframe = client.KLINE_INTERVAL_1MINUTE
    elif timeframe == '15m':
        timeframe = client.KLINE_INTERVAL_15MINUTE
    elif timeframe == '1h':
        timeframe = client.KLINE_INTERVAL_1HOUR
    elif timeframe == '2h':
        timeframe = client.KLINE_INTERVAL_2HOUR
    elif timeframe == '4h':
        timeframe = client.KLINE_INTERVAL_4HOUR
    elif timeframe == '1d':
        timeframe = client.KLINE_INTERVAL_1DAY
    
    #création des bougies passées:
    klines = client.get_historical_klines(pair, timeframe, Starttime)
    Lopen = []
    Lhigh = []
    Llow = []
    Lclose = []
    Ldates = []
    #création des liste pour la base de données
    for k in klines:
        Lopen.append(float(k[1])) #Open
        Lhigh.append(float(k[2])) #High
        Llow.append(float(k[3])) #Low
        Lclose.append(float(k[4])) #Close
        Ldates.append(int(k[0]/1000))

    d = {'date': Ldates, 'open' : Lopen, 'high' : Lhigh, 'low' : Llow, 'price' : Lclose}
    
    df = pd.DataFrame(d)
    dataframe = df.reset_index(drop = True)
    if timeframe != '1m':
        ind.PSAR(dataframe)
        ind.zscore(dataframe, 20, "price")
        ind.sma(dataframe,20, '20Zscore_price')
        ind.sma(dataframe, 7, 'price')
        ind.MACD(dataframe, 'price')
    


    return dataframe

def update():
    try :
        path = "./dataframes/"
        nomfichierdata = input('Entrez le nom de fichier EXACT : ')
        dataframe_update = pd.read_pickle(path + nomfichierdata)
    except Exception:
        print('Le nom du fichier n\'est pas correct vérifiez et re-essayer')
        return
    indice = nomfichierdata.find('mois')
    timeframe = nomfichierdata[indice+4:indice + 6]
    if timeframe == '15':
        timeframe = '15m'
    pair = checkasset(nomfichierdata, timeframe)
    cutupdate = (dataframe_update.loc[len(dataframe_update)-1, 'date'] + getpasindex(timeframe))
    startupdate = str((dataframe_update.loc[len(dataframe_update)-1, 'date'] - getstartindex(timeframe))*1000)
    datatoappend  = dataframe(nomfichierdata, timeframe, startupdate, False,pair)
    cutindex = datatoappend.index[datatoappend['date'] == cutupdate].tolist()[0]
    datato = datatoappend.iloc[cutindex:len(datatoappend)-1]
    dataframenew= pd.concat([dataframe_update,datato])
    dataframenew = dataframenew.reset_index(drop = True)
    lengthofdataframe = round((int(time.time()) - dataframe_update.loc[0,'date'])/(3600*24*30),1)
    nouveaunom = 'dataframe' + str(lengthofdataframe) + nomfichierdata[indice:]
    dataframenew.to_pickle(nouveaunom)

def checkasset(string : str,timeframe : str):
    string = string[::-1]
    timeframe = timeframe[::-1]
    ind = string.find(timeframe)
    asset = string[0:ind]
    return asset[::-1]


def getstartindex(timeframe):
        pas = 0
        if timeframe == '1m':
            pas = 200 * 60
        elif timeframe == '5m':
            pas =  200 * 300
        elif timeframe == '15m':
            pas = 200 * 15 * 60
        elif timeframe == '1h':
            pas = 200 * 60 * 60
        elif timeframe == '2h':
            pas = 200 * 60 * 120
        elif timeframe == '4h':
            pas = 200 * 60 * 60 * 4
        elif timeframe == '1d':
            pas = 200 * 60 * 60 * 24
        return pas

def getpasindex(timeframe):
        pas = 0
        if timeframe == '1m':
            pas = 60
        elif timeframe == '5m':
            pas =  300
        elif timeframe == '15m':
            pas = 15 * 60
        elif timeframe == '1h':
            pas = 60 * 60
        elif timeframe == '2h':
            pas = 60 * 120
        elif timeframe == '4h':
            pas = 60 * 60 * 4
        elif timeframe == '1d':
            pas = 60 * 60 * 24
        return pas
"""
Ci dessus est le code juste pour permettre à l'utilisateur de rentrer les données pour créer la dataframe qui est intéréssante à backtester
Il suffit de répondre aux questions possées lors du lancement du code 
Il y a une gestion des erreurs dans le cas ou les données proposées ne correspondent pas aux données attendus
"""

def delete_column():
    try :
        path = "./dataframes/"
        nomfichierdata = input('Entrez le nom de fichier EXACT : ')
        df = pd.read_pickle(path + nomfichierdata)
    except Exception:
        print('Le nom du fichier n\'est pas correct vérifiez et re-essayer')
        return
    print('Columns list : ')
    print(df.columns)
    column = input('Input a column to delete : ')
    df.drop(column, axis=1, inplace=True)
    print(' Column has been deleted')
    df.to_pickle(nomfichierdata)


def __main__():
    path = "./dataframe/"
    backtest = input("Voulez vous download une dataframe? (True or False) ")
    if backtest == 'True':
        timeframe = input("Choisissez une timeframe : (1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d) ")
        timestart = input("Choisissez un temps unix en milliseconde pour démarer la création de dataframe : ")
        try:
            timestart = int(timestart)
            test1 = timestart/(10**12)
            if int(test1) !=1:
                timestart = 1629756000000 #valeur par défault
                print('timestart value is not usuable default value 1629756000000 has been used')
            test2 = timestart - ceil(timestart/10)*10
            if int(test2) != 0:
                timestart = 1629756000000 #valeur par défault
                print('timestart value is not usuable default value 1629756000000 has been used')
        except:
            timestart = 1629756000000
            print('timestart value is not usuable default value 1629756000000 has been used')
        paire = input('Choisissez la paire pour la base de données (Ex: BTCUSDT) : ')
        lengthofdataframe = round((int(time.time()) - timestart/1000)/(3600*24*30),1)
        name = "dataframe" + str(lengthofdataframe) + 'mois' + timeframe + paire
        dataframe1 = dataframe(name, timeframe, timestart, True, paire)
        dataframe1.to_pickle(path  +name)
    else:
        update1 = input('Voulez vous mettre à jour une dataframe ? (True ou False) ')
        if update1 == 'True':
            update()
        else : 
            modify = input('Voulez vous retirer une colonne d\'une dataframe ? (True ou False) ')
            if modify:
                delete_column()

__main__()

"""
# TESTS NON UTILES
"""