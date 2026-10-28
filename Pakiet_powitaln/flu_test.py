from pathlib import Path
import pandas as pd
from flu_predict import flu_predict

# folder z danymi; zakładamy, że wszystkie pliki zostały już wcześniej pobrane
DATA_FOLDER = Path(__file__).resolve().parent / 'Data'

WEEKS_FORECAST = [3, 4, 5, 6, 7]

def flu_error(year: int, region: str, forecast: list[float], ground_truth: list[float], ground_truth_weeks: list[int]) -> float:
    '''
    Błąd między prognozą `forecast` a danymi referencyjnymi `ground_truth` dla konkretnego województwa i roku. 
    Parametr `ground_truth_weeks` zawiera informację o tym, dla których tygodni faktycznie liczyć błąd (bo na przykład nie wszystkie wartości dla `ground_truth` udało się pobrać). Dane w liście `ground_truth` zawierają tylko dane odpowiadające `ground_truth_weeks`. 
    '''

    # Na wszelki wypadek... gdy są ewidentne niezgodności w ground_truth, kończymy program
    if len(ground_truth) != len(ground_truth_weeks):
        raise SystemExit('Błąd: liczba wartości referencyjnych nie zgadza się z liczbą tygodni!')
    if not all(w in WEEKS_FORECAST for w in ground_truth_weeks):
        raise SystemExit("Błąd: ground_truth_weeks spoza WEEKS_FORECAST!")

    # prognoza w `forecast` to ewidentnie nie to, co trzeba... (uprzejmie nie sprawdzamy typu, dając szansę obliczenia błędu) 
    if len(forecast) != len(WEEKS_FORECAST):
        raise ValueError(f'flu_predict zwraca wynik długości {len(forecast)}')

    error = 0.0
    b = WEEKS_FORECAST[0]
    for gt, w in zip(ground_truth, ground_truth_weeks): # ograniczamy się tylko do dostępnych danych referencyjnych
        fc = forecast[w-b]
        e = fc - gt
        print(f'{region} {year} tydz {w:02d} | progn {fc:.2f} | fakt {gt:.2f} | różnica = {e:.2f}')
        error = error + abs(e)
    print(f'\nBłąd prognozy dla województwa {region} w roku {year} w tygodniach {ground_truth_weeks}: {error:.2f}')
    return error

def flu_total_error(year: int, regions_large: list[str], regions_small: list[str]) -> float:
    '''
    Liczymy błędy dla wskazanych województw, a następnie sumujemy je
    UWAGA: zakładamy, że odpowiednie pliki z danymi zostały już wcześniej pobrane, a dane wejściowe są kompletne.
    '''
    total_error = 0.0
    regions = regions_large + regions_small
    for region in regions:
        infected_filename = str(DATA_FOLDER / f'{year}-{region}-infected-data.csv')
        vaccinated_filename = str(DATA_FOLDER / f'{year}-{region}-vaccinated-data.csv')
        weather_filename = str(DATA_FOLDER / f'{year}-{region}-weather-data.csv')
        try:
            infected_forecast = flu_predict(year, region, infected_filename, vaccinated_filename, weather_filename)
        except Exception as e:
            print(f'Błąd wywołania funkcji flu_predict({year}, {region}, {infected_filename}, {vaccinated_filename}, {weather_filename}) | {e}')
            infected_forecast = [0.0]*5

        infected_observed_filename = str(DATA_FOLDER / f'{year}-{region}-infected-forecast.csv')
        df_infected_observed = pd.read_csv(infected_observed_filename)
        infected_observed = df_infected_observed['Liczba przypadków na 100k'].tolist()
        weeks_observed = df_infected_observed['Numer tygodnia'].tolist()
        
        try:
            err = flu_error(year, region, infected_forecast, infected_observed, weeks_observed)
        except Exception as e:
            print(f'Błąd wywołania funkcji flu_error({year}, {region}, {infected_forecast}, {infected_observed}, {weeks_observed}) | {e}')
            print(f'Typ wyniku prognozy z flu_predict: {type(infected_forecast).__name__}')
            err = sum(infected_observed) # odpowiada sytuacji, że infected_forecast = [0.0]*5
        total_error += err
        print()

    return total_error

if __name__ == "__main__":
    # Będziemy testować cztery województwa: dwa "duże" i dwa "małe". Poniżej - wartości przykładowe
    REGIONS_LARGE = ["ŚLĄSKIE", "MAZOWIECKIE"]
    REGIONS_SMALL = ["OPOLSKIE", "PODLASKIE"]
    
    YEAR = 2026 # Ostateczny test modelu będzie oczywiście dla roku 2027

    print(f'\nBłąd całkowity dla testowanych województw: {flu_total_error(YEAR, REGIONS_LARGE, REGIONS_SMALL):.2f}')
    
