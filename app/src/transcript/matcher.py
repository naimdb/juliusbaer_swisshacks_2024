import json
import csv
from datetime import datetime
from fuzzywuzzy import fuzz

def calculate_similarity(str1, str2):
    return fuzz.ratio(str1.lower(), str2.lower())

def compare_dates(date1, date2):
    try:
        d1 = datetime.strptime(date1, "%dth of %B %Y")
        d2 = datetime.strptime(date2, "%Y-%m-%d")
        return 100 if d1 == d2 else 0
    except ValueError:
        print(f"Erreur de format de date: {date1} ou {date2}")
        return 0

def calculate_score(json_data, csv_row):
    total_score = 0
    total_weight = 0

    weights = {
        "Name": 3,
        "Degree": 2,
        "Date of Birth": 2,
        "ID": 1
    }

    mapping = {
        "Name": "name",
        "Date of Birth": "birthday",
        "Degree": "highest_previous_education",
        "ID": "account_nr"
    }

    scores = {}

    for json_key, csv_key in mapping.items():
        if json_key in json_data and csv_key in csv_row:
            weight = weights.get(json_key, 1)
            if json_key == "Date of Birth":
                score = compare_dates(json_data[json_key], csv_row[csv_key])
            else:
                score = calculate_similarity(str(json_data[json_key]), str(csv_row[csv_key]))
            total_score += score * weight
            total_weight += weight
            scores[json_key] = score

    return total_score / total_weight if total_weight > 0 else 0, scores

def find_best_match(json_data, csv_data):
    best_match = None
    best_score = 0

    for row in csv_data:
        score, details = calculate_score(json_data, row)
        if score > best_score:
            best_score = score
            best_match = row

    return best_match, best_score, details

# Charger les données JSON
try:
    with open('extracted_info.json', 'r') as json_file:
        json_data_list = json.load(json_file)
    print(f"Nombre d'éléments JSON chargés: {len(json_data_list)}")
except Exception as e:
    print(f"Erreur lors de la lecture du fichier JSON: {e}")
    exit()

# Lire le fichier CSV
try:
    with open('client_features.csv', 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        csv_data = list(csv_reader)
    print(f"Nombre de lignes dans le CSV: {len(csv_data)}")
except Exception as e:
    print(f"Erreur lors de la lecture du fichier CSV: {e}")
    exit()

# Traiter chaque élément JSON
for i, json_data in enumerate(json_data_list):
    print(f"\nTraitement de l'élément JSON #{i+1}:")
    best_match, best_score, details = find_best_match(json_data, csv_data)
    
    if best_match:
        print(f"Meilleure correspondance trouvée avec un score de {best_score:.2f}:")
        print(json.dumps(best_match, indent=2))
        print("Détails du score:")
        for key, score in details.items():
            print(f"{key}: {score:.2f}")
    else:
        print("Aucune correspondance trouvée.")

    print(f"JSON original:")
    print(json.dumps(json_data, indent=2))
    print("-" * 50)