import csv
import json
import os
from groq import Groq
import traceback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results_path = os.path.join(BASE_DIR, 'wrong_info', 'wrong_info_results.csv')
print(results_path)
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
    transcript_dir = "../audio_clips"
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
        full_name = get_name_by_id(transcript_id)
        if not full_name:
            print(f"Warning: No matching name found for transcript ID: {transcript_id}")
            return None, None

        row_data = get_row_data(client_data_file, full_name)
        if not row_data:
            print(f"Warning: No data found for {full_name}")
            return None, None

        transcript = load_transcript(transcript_id)
        if not transcript:
            print(f"Warning: Failed to load transcript for ID: {transcript_id}")
            return None, None

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

def write_result(transcript_id, result):
    results_path = os.path.join(BASE_DIR, 'wrong_info', 'fact_check_results.csv')
    
    # Check if exists, if not, create it with headers
    file_exists = os.path.isfile(results_path)
    
    with open(results_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write headers if file is newly created
        if not file_exists:
            writer.writerow(['rec_id', 'result'])
        
        writer.writerow([transcript_id, 'TRUE' if result else 'FALSE'])

def process_transcript(client_data_file, transcript_id):
    client = Groq(api_key="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")
    
    full_name, result = check_facts(transcript_id, client_data_file, client)
    
    if full_name and result is not None:
        write_result(transcript_id, result)
        print(f"Result for transcript {transcript_id} has been written to fact_check_results.csv")
    else:
        print(f"Unable to process transcript {transcript_id}")
    
    return not result

def run_fact_check(client_data_file, transcript_id):
    load_transcript_data()
    return process_transcript(client_data_file, transcript_id)

# Usage
client_data_file = os.path.join(BASE_DIR, "client_profiles", "client_features.csv")
transcript_id = "your_transcript_id_here"  # Replace with actual transcript ID
result = run_fact_check(client_data_file, transcript_id)
print(f"Fact check result for {transcript_id}: {'Passed' if result else 'Failed'}")
