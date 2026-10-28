# %%

from datetime import date, datetime
from pathlib import Path
import requests

import pandas as pd

DATA_FOLDER = Path(__file__).resolve().parent / 'Data'
DATA_FOLDER.mkdir(parents=True, exist_ok=True)

REGIONS = {
    "DOLNOŚLĄSKIE": "Wrocław",
    "KUJAWSKO-POMORSKIE": "Toruń",
    "LUBELSKIE": "Lublin",
    "LUBUSKIE": "Zielona Góra",
    "ŁÓDZKIE": "Łódź",
    "MAŁOPOLSKIE": "Kraków",
    "MAZOWIECKIE": "Warszawa",
    "OPOLSKIE": "Opole",
    "PODKARPACKIE": "Rzeszów",
    "PODLASKIE": "Białystok",
    "POMORSKIE": "Gdańsk",
    "ŚLĄSKIE": "Katowice",
    "ŚWIĘTOKRZYSKIE": "Kielce",
    "WARMIŃSKO-MAZURSKIE": "Olsztyn",
    "WIELKOPOLSKIE": "Poznań",
    "ZACHODNIOPOMORSKIE": "Szczecin",
}

def fetch_city_coords(city: str) -> tuple[float, float]:
    '''
    Zwraca współrzędne geograficzne (lat, lon) dla miasta city, pobrane z open-meteo
    '''
    url = 'https://geocoding-api.open-meteo.com/v1/search'
    params = {
        "name": city, 
        "count": 1, 
        "language": "pl", 
        "format": "json"
    }
    print(f'Pobieram współrzędne dla miasta {city} z portalu open-meteo.com')
    data = requests.get(url, params=params, timeout=5).json()
    results = data.get('results')
    if not results:
        raise ValueError('Błąd!')
    lat = float(results[0]['latitude'])
    lon = float(results[0]['longitude'])
    return (lat, lon)

def fetch_weather_data(year: int, region: str, weather_date_range: tuple[str, str], coords: tuple[float, float] | None = None) -> pd.DataFrame:
    '''
    Pobiera z open-meteo dane pogodowe dla stolicy województwa `region`.
    Uwaga: parametr `year` oznacza rok *prognozy* w konkursie, więc dane będą dotyczyły ostatnich czterech tygodni (ISO) roku `year-1`.
    Pierwszy i ostatni dzień tego okresu jest przekazany w liście `weather_date_range`.
    Pobrane dane zapisuje do pliku CSV o nazwie `year`-`region`-weather-data.csv i jednocześnie zwraca ramkę Pandas zawierającą te dane.
    Uwaga: przyjmujemy konwencję, że rok w nazwie pliku odpowiada rokowi *prognozy*.
    '''
    city = REGIONS[region]
    weather_path = DATA_FOLDER / f'{year}-{region}-weather-data.csv' # przyjmujemy konwencję, że rok w nazwie pliku odpowiada rokowi *prognozy*
    if coords is None:
        coords = fetch_city_coords(city)
    lat, lon = coords
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": weather_date_range[0],
        "end_date":  weather_date_range[1],
        "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code",
        "timezone": "auto",
        "format": "csv",
    }
    url = "https://archive-api.open-meteo.com/v1/archive"
    try:
        url_weather = requests.get(url, params=params, timeout=5).url
        print('Pobieram dane pogodowe z portalu open-meteo.com')
        print(f'\t{city} ({lat}, {lon}) | {weather_date_range[0]} ... {weather_date_range[1]}')
        df_weather = pd.read_csv(url_weather, skiprows=3)
    except Exception as e:
        print(f'\tNie udało się pobrać! | {e}')
        df_weather = pd.DataFrame(columns=["time","temperature_2m (°C)","relative_humidity_2m (%)","apparent_temperature (°C)","precipitation (mm)","weather_code (wmo code)"])
    if df_weather.empty:
        print('\tNie zapisuję: brak danych!')
    else:
        print(f'\tZapisuję do {weather_path.name}')
        df_weather.to_csv(weather_path, index=False, encoding='utf-8-sig')
    return df_weather

def fetch_flu_data(source_sheets: dict[str, pd.DataFrame], year: int, region: str, mode: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    '''
    Z arkusza Excela `source_sheets` (pobranego z portalu `ezdrowie.gov.pl`) wybiera i zapisuje do pliku CSV dane, które w zadaniu konkursowym nazywają się `infected` i `vaccinated`. Dodatkowo funkcja zwraca jako wynik ramki Pandas z tymi danymi. 

    Parametry `region` i `year` są traktowane tak jak w zadaniu, dlatego w zależności od trybu działania `mode`:
    
    * jeżeli `mode` == `forecast`, zbieramy dane odpowiadające okresowi prognozowanemu, czyli 
        * dla zachorowań: tygodniom (3,4,5,6,7) roku `year` 
        * dla szczepień: miesiącom (1,2) roku `year` (są to dane niewykorzystywane w zadaniu: nie prognozujemy szczepień)
    * jeżeli `mode` == `data`, zbieramy dane wejściowe dla modelu, czyli 
        * dla zachorowań: z ostatnich czterech tygodni roku `year-1` 
        * dla szczepień: z miesięcy (8,9,10,11) roku `year-1` 
    '''
    print(f'Wybieram dane z arkusza Excela z portalu ezdrowie.gov.pl ({mode = })')
    # najpierw wczytujemy odpowiednie arkusze do ramek Pandas 
    df_infected = source_sheets["Tabela 3"]
    df_vaccinated = source_sheets["Tabela 5"]

    # ustalamy okresy jakie nas interesują
    if mode == 'forecast':
        weeks, months = get_forecast_params(year)
        source_year = year # rok, który nas interesuje
    elif mode == 'data':
        weeks, months, _ = get_data_params(year)
        source_year = year-1 # dane **wejściowe** dla modelu pochodzą z poprzedniego roku!
    else:
        raise ValueError(f'Nieznany parametr: {mode = }')
    
    # ograniczamy dane o zachorowaniach do interesującego nas zakresu
    mask_infected = (
        (df_infected["Województwo"] == region.upper())
        & (df_infected["Choroba"] == "Grypa")
        & (df_infected["Rok"] == source_year)
        & (df_infected["Numer tygodnia"].isin(weeks))
    )
    df_infected = df_infected[mask_infected].copy()
    
    # ograniczamy dane o szczepieniach do interesującego nas zakresu, dostosowując się do formatu danych z ezdrowie.gov.pl
    start_month =  f"{source_year}-{months[0]:02d}-01"
    end_month   =  f"{source_year}-{months[-1]:02d}-01"
    mask_vaccinated = (
        (df_vaccinated["Województwo"] == region.upper())
        & (df_vaccinated["Choroba"] == "Grypa")
        & (df_vaccinated["Miesiąc"] >= start_month)
        & (df_vaccinated["Miesiąc"] <= end_month)
    )
    df_vaccinated = df_vaccinated[mask_vaccinated].copy()

    infected_path = DATA_FOLDER / f'{year}-{region}-infected-{mode}.csv'
    vaccinated_path = DATA_FOLDER / f'{year}-{region}-vaccinated-{mode}.csv'
    
    print(f'\tZachorowania dla: rok {source_year} tygodnie: {weeks}')
    if not df_infected.empty:
        print(f'\tZapisuję do {infected_path.name}')
        df_infected.to_csv(infected_path, index=False, encoding='utf-8-sig')
    else:
        print('\tNie zapisuję: brak danych!')
    print(f'\tSzczepienia dla: rok {source_year} miesiące: {months}')
    if not df_vaccinated.empty:
        print(f'\tZapisuję do {vaccinated_path.name}')
        df_vaccinated.to_csv(vaccinated_path, index=False, encoding='utf-8-sig')
    else:
        print('\tNie zapisuję: brak danych!')
    return df_infected, df_vaccinated

def get_data_params(year: int) ->  tuple[list[int], list[int], tuple[str, str]]:
    '''
    Dla modelu prognozującego na rok `year` ustalamy, jakie konkretnie 
    tygodnie, miesiące i dni roku `year-1` mają zostać użyte do pobrania danych dla modelu, dla - odpowiednio - liczby zachorowań, szczepień i danych pogodowych.
    '''
    infected_last_week = date(year-1, 12, 28).isocalendar().week # the last week of the year
    infected_weeks = list(range(infected_last_week-3, infected_last_week+1))
    vaccinated_months = [8, 9, 10, 11]
    weather_date_range = ( 
        datetime.strptime(f'{year-1}-W{infected_weeks[0]}-1',  "%G-W%V-%u").strftime('%Y-%m-%d'), 
        datetime.strptime(f'{year-1}-W{infected_weeks[-1]}-7', "%G-W%V-%u").strftime('%Y-%m-%d')
    )
    return infected_weeks, vaccinated_months, weather_date_range
    
def get_forecast_params(year: int) ->  tuple[list[int], list[int]]:
    '''
    Dla modelu prognozującego na rok `year` ustalamy, jakich konkretnie 
    tygodni i miesięcy roku `year` ma dotyczyć prognoza. 
    Informacja o miesiącach nie jest używana w konkursie.
    '''
    infected_weeks_forecast = [3, 4, 5, 6, 7]
    vaccinated_months_forecast = [1, 2]
    return infected_weeks_forecast, vaccinated_months_forecast
    
def print_run_params(year: int, region: str, infected_weeks: list[int], vaccinated_months: list[int], weather_date_range: tuple[str, str], city: str, infected_weeks_forecast: list[int]) -> None:
    print()
    print('='*40)
    print(f'Prognoza: województwo {region}, rok {year}, tygodnie {infected_weeks_forecast}')
    print('Dane wejściowe:')
    print(f'\tZachorowania: rok {year-1}, tygodnie {infected_weeks}')
    print(f'\tSzczepienia:  rok {year-1}, miesiące {vaccinated_months}')
    print(f'\tPogoda:       miasto {city}, dni {weather_date_range[0]} ... {weather_date_range[1]}')
    print('-'*40)

def collect_all() -> None:
    '''
    Pobiera wszystkie możliwe dane dla konkursowego modelu dostępne w ezdrowie.gov.pl - zarówno dla okresu z danymi modelu, jak i dla okresu prognozowanego.
    Zapisuje to wszystko do plików CSV w folderze `Data`.
    '''
    print('Pobieram pełny arkusz Excela z portalu ezdrowie.gov.pl... (to może potrwać)')
    url = 'https://ezdrowie.gov.pl/pobierz/14553'
    source_sheets  = pd.read_excel(url, sheet_name=["Tabela 3", "Tabela 5"], skiprows=5)
    
     # zbieramy współrzędne wszystkich stolic województw, bo przydadzą się wielokrotnie
    city_coords_by_name = {} 
    for region, city in REGIONS.items():
        coords = fetch_city_coords(city)
        city_coords_by_name[city] = coords
        
    for year in range(2025,2028):
        infected_weeks, vaccinated_months, weather_date_range = get_data_params(year)
        infected_weeks_forecast, vaccinated_months_forecast = get_forecast_params(year)
        for region, city in REGIONS.items():
            print_run_params(year, region, infected_weeks, vaccinated_months, weather_date_range, city, infected_weeks_forecast)
            df_weather = fetch_weather_data(year, region, weather_date_range, city_coords_by_name[city])
            df_infected, df_vaccinated = fetch_flu_data(source_sheets, year, region, 'data')
            df_infected_forecast, df_vaccinated_forecast = fetch_flu_data(source_sheets, year, region, 'forecast')
            print('Gotowe. Poniżej fragment danych wejściowych i danych prognozowanych:')
            print(df_infected.head())
            print(df_infected_forecast.head())

if __name__ == "__main__":
    collect_all()

# %%
