import os
import json
import time
from groq import Groq
from jsonpatch import JsonPatch

client = Groq(api_key=os.environ["GROQ_API_KEY"])

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
INPUT_DIR = os.path.join(BASE_DIR, "audio_clips")
OUTPUT_DIR = os.path.join(BASE_DIR, "json")
TEMP_DIR = os.path.join(BASE_DIR, "tmp")

def get_info(item, file_id):
    prompt = """Can you extract the name of the person calling? Also retrieve birthday, marital status, account number, tax residency, net worth in millions, profession, social security number, relationship manager. Everything should be in a JSON file with the ID. Here's the input:

{item}

Please structure your response as a JSON object with fields for 'ID', 'Name', 'birthday', 'marital_status', 'account_nr', 'tax_residency', 'net_worth_in_millions', 'profession', 'social_security_number' and 'relationship_manager'. Only include fields in the JSON if the information is available in the input. Do not include fields with null or empty values. Use "{file_id}" as the ID."""

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are an assistant that extracts structured information from text and responds only with a JSON object."
            },
            {
                "role": "user",
                "content": prompt.format(item=item, file_id=file_id)
            }
        ],
        model="mixtral-8x7b-32768",
        temperature=0.2,
        max_tokens=300,
    )
    
    return chat_completion.choices[0].message.content

def process_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
        
        translated_text = json_data.get('result', {}).get('translated_text')
        
        if translated_text:
            file_id = os.path.splitext(os.path.basename(file_path))[0]
            info = get_info(translated_text, file_id)
            try:
                info_dict = json.loads(info)
                info_dict = {k: v for k, v in info_dict.items() if v not in (None, "", "null")}
                
                patch = JsonPatch([
                    {"op": "add", "path": "/context", "value": info_dict}
                ])
                
                patched_json = patch.apply(json_data)
                
                with open(file_path, 'w', encoding='utf-8') as outfile:
                    json.dump(patched_json, outfile, indent=2, ensure_ascii=False)
                
                print(f"Processed and updated: {file_path}")
            except json.JSONDecodeError:
                print(f"JSON parsing error for file: {file_path}")
                print(f"Received response: {info}")
        else:
            print(f"No translated text found in: {file_path}")

    except UnicodeDecodeError:
        print(f"UTF-8 decoding error for file: {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    for filename in os.listdir(OUTPUT_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(OUTPUT_DIR, filename)
            process_json_file(file_path)
            time.sleep(2)  # Adding a delay to avoid rate limiting

if __name__ == "__main__":
    main()