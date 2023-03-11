from pickle import TRUE
from pandas import *
import pandas as pd
from binance import *
import asyncio
from matplotlib import *
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime
from math import *
import automatisationbacktest as aut
import Indicateursbacktest as ind

def Selecttime(dataframe,startime, endtime):
    Lx = []
    for k in range(startime,endtime+1):
        
        Lx.append(dataframe.loc[k,'date'])
    return Lx

#importation des dataframe pour le backtest:
path = './dataframes'
input_dataframe = path + "/dataframe17.9mois15mBTCUSDT"
dataframe6mois5m = pd.read_pickle(input_dataframe)
dataframe6mois1m = pd.read_pickle(path + "/dataframe17.9mois1mBTCUSDT")

for k in range(len(input_dataframe)):
    if input_dataframe[k:k+4] == 'mois' :
        if input_dataframe[k+6] == 'm' : 
            timeframe = input_dataframe[k+4:k+7]
        else:
            timeframe = input_dataframe[k+4:k+6]
# print(list(dataframe6mois5m.columns))
# Initialisation de liste pour différentes représenations graphiques
LCapital = []
Lprice = []
Lindex = []
async def main(filename,backtest,start,end):
    #Valeurs de TP/SL pour la stratégie (a adapter en fonction de la stratégie à bakctester)
    TP = 0.01
    SL = 0.005
    typetrade = 'long'
    #On veut avoir le nombre de trade
    nombreDeTrade = 0
    #Variable pour utile dans certaines stratégies
    Bornes = 0
    #Variable de teste pour savoir si un trade est en cours ou pas
    enCours = False
    #On initialise le capital de départ à 1000
    Capital = 1000
    longpossibility = False
    shortpossibility = False

    if backtest == 'True':

        Gainmoyentrade = 0 
        Winrate = 0
        k = start
        #On instancie un objet backtest avec les données acutelles, elles seront modifiées à chaques entré dans un trade
        back1 = aut.backtest(dataframe6mois5m, dataframe6mois1m, filename,\
        TP, SL, k, end , enCours, Capital, nombreDeTrade, Winrate, Gainmoyentrade, Lindex ,Lprice, LCapital)
        ZSCOREEMA = dataframe6mois5m['20Zscore_price'].ewm(span = 14 , adjust = False).mean()
        #On parcourt toute la dataframe
        while k < end:
            """"
            On parcourt toute la dataframe

            A chaque étape on change les variables essentiels dans le backtesting (puisqu'elles sont différentes pour tout k). 
            Ici on peut initialiser des conditions pour ouvrir des shorts et des longues, enfaite on va définir la stratégie à backtester
            
            Toutes les valeurs numériques sont changeable, elles sont choisis car c'est celles qui donnent les meilleurs rendement mais  
            il peut en exister des meilleurs

            /!\ Si du code est commenté c'est qu'il est souvent utile mais pas dans le dernier cas testé. 
            """
            enCours = False
            #Ici on met à jour les informations importantes dans le backtest à chaque itération
            back1.updateL(back1.Capital,datetime.utcfromtimestamp(dataframe6mois5m.loc[int(k),'date']).strftime('%Y-%m-%d %H:%M:%S'),dataframe6mois5m.loc[int(k),'price'])

            
            """ Code commenté utile dans certaines stratégies"""
            if dataframe6mois5m.loc[int(k),'20Zscore_price'] >= 3: #Ici code pour startégie zscore
                shortpossibility = True
            elif dataframe6mois5m.loc[int(k),'20Zscore_price'] <= 0:
                shortpossibility = False
            if dataframe6mois5m.loc[int(k),'20Zscore_price'] <= -3 :
                longpossibility = True
            elif dataframe6mois5m.loc[int(k),'20Zscore_price'] >= 0:
                longpossibility = False
            """ Fin Code commenté utile dans certaiens stratégies"""

            #On définit les entrées dans un trade (entrée long =/= de entrée short)
            
            Entryconditionshort = shortpossibility and dataframe6mois5m.loc[int(k-1), '20Zscore_price'] > dataframe6mois5m.loc[int(k), '20Zscore_price'] and ZSCOREEMA[k] > dataframe6mois5m.loc[int(k), '20Zscore_price']
            Entryconditionlong = False #longpossibility and dataframe6mois5m.loc[int(k-1), '20Zscore_price'] < dataframe6mois5m.loc[int(k), '20Zscore_price'] and ZSCOREEMA[k] < dataframe6mois5m.loc[int(k), '20Zscore_price'] and dataframe6mois5m.loc[k,'PSARdir'] == 'bull'
            
            # longpossibility and dataframe6mois5m.loc[int(k-1), '20Zscore_price'] < dataframe6mois5m.loc[int(k), '20Zscore_price'] and dataframe6mois5m.loc[int(k), '20SMA_20Zscore_price'] < dataframe6mois5m.loc[int(k), '20Zscore_price']
            # shortpossibility and dataframe6mois5m.loc[int(k-1), '20Zscore_price'] > dataframe6mois5m.loc[int(k), '20Zscore_price'] and dataframe6mois5m.loc[int(k), '20SMA_20Zscore_price'] > dataframe6mois5m.loc[int(k), '20Zscore_price']
            #Si les conditions précédentes sont réalisées alors on rentre dans un trade et on entre aussi dans la partie automatique du backetesting
            #la base de donnée va etre parcouru à la recherche d'une condition de sortie
            #L'inconvenient c'est que les conditions de sorties outre TP et SL doivent etre mentionner dans automatisaiont_backtest() avant le début du bakctest
            #
            if Entryconditionshort and not Entryconditionlong:
                typetrade = 'short'
                enCours = True
                #Il faut ici changer la timeframe en fonction de sur quelle timeframe est la stratégie principale. 
                back1.automatisation_backtest(TP , SL, typetrade, Entryconditionshort, Entryconditionlong, k, enCours, timeframe, Lindex, Lprice, LCapital, True)
                k = back1.indice
                shortpossibility = False
            
            if Entryconditionlong and not Entryconditionshort:
                typetrade = 'long'
                enCours = True
                back1.automatisation_backtest(TP , SL, typetrade, Entryconditionlong, Entryconditionlong, k, enCours, timeframe, Lindex, Lprice, LCapital)
                k = back1.indice
                longpossibility = False
            k+=1
                
#sauvegarde de variables utiles pour juger de la viabilité d'une stratégie
    try:
        Winrate = (back1.Winrate / back1.nombreDeTrade) * 100
    except :
        Winrate = 0

    print("nombre de trade: " + str(back1.nombreDeTrade))
    try:
        print("gain moyen par trade: " + str(back1.Gainmoyentrade/back1.nombreDeTrade))
    except:
        print("gain moyen par trade: 0")
    print("Winrate: " + str(Winrate) + "%")
    # print(dataframe6mois5m.iloc[debut:fin,13].tolist())
    # print(Lindex)
    x = matplotlib.dates.date2num(Lindex)
    formater = matplotlib.dates.DateFormatter('%Y-%m-%d')

    figure = plt.figure()
    axes1 = figure.add_subplot(2, 1, 1)
    axes1.xaxis.set_major_formatter(formater)
    axes1.set_xlabel('Time')
    axes1.set_ylabel('Capital Evolution')
    axes1.tick_params(labelrotation=15)
    axes1.plot(x, back1.LCapital)

    axes2 = figure.add_subplot(2, 1, 2)
    axes2.xaxis.set_major_formatter(formater)
    axes2.set_xlabel('Time')
    axes2.set_ylabel('')
    axes2.tick_params(labelrotation=15)
    axes2.plot(x, Lprice)

    # axes3 = figure.add_subplot(3, 1, 3)
    # axes3.xaxis.set_major_formatter(formater)
    # axes3.set_xlabel('Time')
    # axes3.set_ylabel('Zscore')
    # axes3.tick_params(labelrotation=15)
    # axes3.plot(x, dataframe6mois5m.iloc[debut:fin,13].tolist())
    
    figure.tight_layout()
    plt.show()
    

a = input("Entrez le nom_du_fichier : ")
if a == '':
    print('Fichier par défaut utilisé : essai.json')
    a = "essai"
a = a + '.json'
datei = datetime.utcfromtimestamp(dataframe6mois5m.loc[0,'date']).strftime('%Y-%m-%d')
datef = datetime.utcfromtimestamp(dataframe6mois5m.loc[len(dataframe6mois5m)-1,'date']).strftime('%Y-%m-%d')
debut = input("Faire le choix de la date de début (de " + datei + " à " +  datef + " ) : ")
fin = input("Faire le choix de la date de fin, doit être supérieur à la date de début et inférieur à " + datef + " : ")
if debut == '' and fin == '':
    
    debut = '2021-08-25'
    fin = '2023-02-09'
    print('Dates par défauts utilisées : debut =  ' + debut + ', fin =  ' + fin)
debut = int(datetime.timestamp(datetime.strptime(debut + ' 00:00:00', '%Y-%m-%d %H:%M:%S')))
fin = int(datetime.timestamp(datetime.strptime(fin + ' 00:00:00', '%Y-%m-%d %H:%M:%S')))

debut = dataframe6mois5m.index[dataframe6mois5m['date'] == debut].tolist()[0]
fin = dataframe6mois5m.index[dataframe6mois5m['date'] == fin].tolist()[0]
asyncio.run(main(a ,'True',debut,fin))


""""

Ici on sauvegarde du code utile pour le backteste d'ancienne stratégie
On a donc des exemples de code intéréssant et réutilisable

"""
#
#cas du bot stratégie 1 
#
# if dataframe6mois5m.loc[int(k),'20Zscore_price'] >= 3:
#    shortpossibility = True
#if dataframe6mois5m.loc[int(k),'20Zscore_price'] <= -3:
#    longpossibility = True
#Entryconditionshort = shortpossibility and dataframe6mois5m.loc[int(k),'20Zscore_price'] < dataframe6mois5m.loc[int(k) - 1, '20Zscore_price'] and dataframe6mois5m.loc[int(k),'20Zscore_price'] < dataframe6mois5m.loc[int(k), '20SMA_20Zscore_price']
#Entryconditionlong = longpossibility and dataframe6mois5m.loc[int(k),'20Zscore_price'] > dataframe6mois5m.loc[int(k) - 1, '20Zscore_price'] and dataframe6mois5m.loc[int(k),'20Zscore_price'] > dataframe6mois5m.loc[int(k), '20SMA_20Zscore_price']

#
#Cas du bot stratégie 2 
#
# if dataframe6mois5m.loc[int(k),'20Zscore_price'] >= 3:
#     shortpossibility = True
# elif dataframe6mois5m.loc[int(k),'20Zscore_price'] <= 1:
#     shortpossibility = False
# if dataframe6mois5m.loc[int(k),'20Zscore_price'] <= -3 :
#     longpossibility = True
# elif dataframe6mois5m.loc[int(k),'20Zscore_price'] >= -1:
#     longpossibility = False
# Entryconditionshort = dataframe6mois5m.loc[int(k),'7SMA_price'] >= dataframe6mois5m.loc[int(k),'20SMA_price'] and shortpossibility and dataframe6mois5m.loc[int(k),'20Zscore_price'] < dataframe6mois5m.loc[int(k) - 1,'20Zscore_price']
# Entryconditionlong = dataframe6mois5m.loc[int(k),'7SMA_price'] <= dataframe6mois5m.loc[int(k),'20SMA_price'] and longpossibility and dataframe6mois5m.loc[int(k),'20Zscore_price'] > dataframe6mois5m.loc[int(k) - 1,'20Zscore_price']