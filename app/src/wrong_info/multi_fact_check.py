import csv
import json
import os
from groq import Groq
import traceback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

transcript_data = {}

results_path = os.path.join(BASE_DIR, 'wrong_info', 'wrong_info_results.csv')
matched_results_path = os.path.join(BASE_DIR, 'impersonator', 'filtered_matched_results.csv')

def load_transcript_data():
    global transcript_data
    try:
        with open(matched_results_path, 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            transcript_data = {row[0]: row[1] for row in csv_reader}
            return transcript_data
    except FileNotFoundError:
        print(f"Error: {matched_results_path} not found.")
    except Exception as e:
        print(f"Error reading {matched_results_path}: {str(e)}")
        print(traceback.format_exc())

def get_name_by_id(transcript_id):
    return transcript_data.get(transcript_id, '')

def get_row_data(client_data_file, full_name):
    try:
        with open(client_data_file, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                if row['name'].lower().strip() == full_name.lower().strip():
                    return row
            print(f"No match found for {full_name}")
    except FileNotFoundError:
        print(f"Error: {client_data_file} not found.")
    except Exception as e:
        print(f"Error reading {client_data_file}: {str(e)}")
        print(traceback.format_exc())
    return None

def load_transcript(transcript_id):
    transcript_dir = os.path.join(BASE_DIR, 'assets', 'json')
    transcript_file = f"{transcript_id}.json"
    try:
        with open(os.path.join(transcript_dir, transcript_file), 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Transcript file {transcript_file} not found in the {transcript_dir} directory.")
    except json.JSONDecodeError:
        print(f"Error: Failed to parse JSON in {transcript_file}")
    except Exception as e:
        print(f"Error reading transcript file {transcript_file}: {str(e)}")
        print(traceback.format_exc())
    return None

def check_facts(transcript_id, client_data_file, client):
    try:
        # Step 1: Get name by id from matched_results.csv
        full_name = get_name_by_id(transcript_id)
        if not full_name:
            print(f"Warning: No matching name found for transcript ID: {transcript_id}")
            return None, None

        # Step 2: Get client data row
        row_data = get_row_data(client_data_file, full_name)
        if not row_data:
            print(f"Warning: No data found for {full_name}")
            return None, None

        # Step 3: Load transcript
        transcript = load_transcript(transcript_id)
        if not transcript:
            print(f"Warning: Failed to load transcript for ID: {transcript_id}")
            return None, None

        # Step 4: Run the analysis
        data_string = ", ".join([f"{k}: {v}" for k, v in row_data.items()])
        try:
            analysis = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze the call transcript by comparing each statement to the provided client data. Follow these rules:\n"
                        "1. Only consider statements that correspond to columns in the client data.\n"
                        "2. For each relevant statement, check if it MATCHES or DOES NOT MATCH the client data.\n"
                        "3. Ignore any statements about urgency, confidentiality, or requests for actions.\n"
                        "4. Do not mark anything as UNVERIFIABLE. Only consider data present in both the transcript and client data.\n"
                        "5. After analysis, conclude with 'output=true' if ALL checked statements match, or 'output=false' if ANY statement does not match.\n"
                        "6. Present your analysis as a list of comparisons, followed by the output."
                    },
                    {
                        "role": "user",
                        "content": f"transcript: {transcript['result']['translated_text']}\n\ndata: {data_string}"
                    }
                ],
                model="llama3-8b-8192",
            )
            output_line = analysis.choices[0].message.content.split('\n')[-1]
            result_str = output_line.split(': ')[-1].lower().strip()
            if (result_str == "output=true" or result_str == "true"):
                result = True
            else:
                result = False
            return full_name, result
        except Exception as e:
            print(f"Error during Groq API call: {str(e)}")
            print(traceback.format_exc())
            return None, None

    except Exception as e:
        print(f"Unexpected error in check_facts: {str(e)}")
        print(traceback.format_exc())
        return None, None

def process_all_transcripts(client_data_file, single_transcript_id=None):
    client = Groq(api_key="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")
    results = []

    if single_transcript_id:
        full_name, result = check_facts(single_transcript_id, client_data_file, client)
        if full_name and result is not None:
            results.append([single_transcript_id, result])
    else:
        transcript_ids = []
        matched_results_path = os.path.join(BASE_DIR, 'impersonator', 'filtered_matched_results.csv')
        with open(matched_results_path, 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                transcript_ids.append(row[0])

        for transcript_id in transcript_ids:
            full_name, result = check_facts(transcript_id, client_data_file, client)
            if full_name and result is not None:
                results.append([transcript_id, result])

    with open(results_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['rec_id', 'result'])
        for rec_id, check_result in results:
            writer.writerow([rec_id, 'TRUE' if check_result else 'FALSE'])

    print(f"Results have been written to {results_path}")
    return results
    
def run_fact_check(client_data_file, single_transcript_id=None):
    load_transcript_data()
    results = process_all_transcripts(client_data_file, single_transcript_id)
    
    all_passed = all(result[1] for result in results)
    # check if all true
    
    return not all_passed

# load_transcript_data()

# client_data_file = os.path.join(BASE_DIR, "client_profiles", "client_features.csv")
# process_all_transcripts(client_data_file)