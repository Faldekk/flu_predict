# 1. INFORMACJE O ZESPOLE I WSPÓŁPRACOWNIKACH

'''
Zespół: Jakub Mikuła
Model: Dzieło nieprzespanych nocy. 
Implementacja: przy pomocy ChatGPT-6 
'''

import numpy as np
import pandas as pd

def flu_predict(year, region, infected, vaccinated, weather):
    df_infected_data = pd.read_csv(infected)
    df_vaccinated_data = pd.read_csv(vaccinated)
    df_weather_data = pd.read_csv(weather)

    df_infected_data = df_infected_data.sort_values(by=["Rok", "Numer tygodnia"])
    print(df_infected_data[["Numer tygodnia", "Liczba przypadków na 100k"]])

    zachor1 = df_infected_data["Liczba przypadków na 100k"]

    df_infected_data["przyrost"] = zachor1.diff() # delta zachorowań
    df_infected_data["tempo"] = zachor1.pct_change() # ułamkowo procenty delta tempa
    srednie_tempo = df_infected_data["tempo"].mean() # średnia ar. z temp
    tempo_geometryczne = (zachor1.iloc[-1] / zachor1.iloc[0]) ** (1/3) - 1 

    tmp1 = df_infected_data["tempo"]
    df_infected_data["zmiana_tempa"] = tmp1.diff() # zmiana tempa dla okresu
    
    
    forecast = [0.0] * 5 
    return forecast

infected = 'Data/2026-ŁÓDZKIE-infected-data.csv'
vaccinated = 'Data/2026-ŁÓDZKIE-vaccinated-data.csv'
weather = 'Data/2026-ŁÓDZKIE-weather-data.csv'

forecast = flu_predict(2026, "ŁÓDZKIE", infected, vaccinated, weather)
