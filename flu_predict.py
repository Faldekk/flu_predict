# 1. INFORMACJE O ZESPOLE I WSPÓŁPRACOWNIKACH

'''
Zespół: Jakub Mikuła
Model: Dzieło nieprzespanych nocy. 
Implementacja: przy pomocy ChatGPT-6 
'''

import numpy as np
import pandas as pd

# Ustawienia do sprawdzenia
region  = "ŁÓDZKIE"
infected = f'Data/2026-{region}-infected-data.csv'
vaccinated = f'Data/2026-{region}-vaccinated-data.csv'
weather = f'Data/2026-{region}-weather-data.csv'

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

    alpha = 0.5

    ostatnie_z = zachor1.iloc[-1]
    ostatnie_tempo = df_infected_data["tempo"].iloc[-1]
    ostatnia_zmiana = df_infected_data["zmiana_tempa"].iloc[-1]

    forecast = []

    for i in range(5):
        prognozowane_tempo = (ostatnie_tempo + alpha * ostatnia_zmiana)
        prognoza = ostatnie_z * (1 + prognozowane_tempo)

        forecast.append(float(prognoza))

        ostatnie_z = prognoza
        ostatnie_tempo = prognozowane_tempo

    # To sztuczne liczby ćwiczeniowe, jeszcze nie historia zachorowań.
    przykladowe_mnozniki = [1.5, 1.2, 2.0]

    k3 = np.median(przykladowe_mnozniki)
    prognoza_t3 = zachorowania.iloc[-1] * k3

    # 7. PODGLĄD OBLICZEŃ — NA CZAS NAUKI

    print("\nDane i obliczone zmiany:")
    print(df_infected_data[
        ["Numer tygodnia", "Liczba przypadków na 100k",
         "przyrost", "tempo", "zmiana_tempa"]
    ])

    print("\nŚrednie tempo:", srednie_tempo)
    print("Tempo geometryczne:", tempo_geometryczne)

    print("\nPięć prognoz z pętli:", forecast)
    print("Osobna prognoza z przykładowego mnożnika:", prognoza_t3)

    return forecast


forecast = flu_predict(2027, region, infected, vaccinated, weather)