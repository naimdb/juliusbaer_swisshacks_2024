import json
import os

JSON_DIR = "/Users/naimdb/JB_SwissHacks/json/"
OUTPUT_FILE = "/Users/naimdb/JB_SwissHacks/translations_summary.txt"

def extract_translations():
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        for filename in os.listdir(JSON_DIR):
            if filename.endswith('.json'):
                file_path = os.path.join(JSON_DIR, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as json_file:
                        data = json.load(json_file)
                    
                    file_name_without_ext = os.path.splitext(filename)[0]
                    
                    translated_text = data['result'].get('translated_text', 'No translation available')
                    
                    outfile.write(f"{file_name_without_ext}: {translated_text}\n")
                    
                    print(f"Processed: {filename}")
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
    
    print(f"Extraction completed. Results saved in {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_translations()