import os
import subprocess
import json
import locale
from transformers import MarianMTModel, MarianTokenizer

FFMPEG_EXEC = "ffmpeg"
WHISPER_EXEC = os.path.expanduser("~/whisper.cpp/main")
MODEL_PATH = os.path.expanduser("~/whisper.cpp/models/ggml-large-v3.bin")
INPUT_DIR = os.path.expanduser("~/JB_SwissHacks/audio/")
OUTPUT_DIR = os.path.expanduser("~/JB_SwissHacks/json/")
TEMP_DIR = os.path.expanduser("~/JB_SwissHacks/tmp/")

def convert_audio(input_file, output_file):
    command = [
        FFMPEG_EXEC,
        "-i", input_file,
        "-ar", "16000",
        output_file
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Conversion successful: {input_file} -> {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error during audio conversion: {e}")
        print(f"Error output: {e.stderr}")

def transcribe_file(input_file, output_json):
    input_dir = os.path.dirname(input_file)
    command = [
        WHISPER_EXEC,
        "-m", MODEL_PATH,
        "-f", input_file,
        "-l", "auto",
        "-oj"
    ]
    try:
        system_encoding = locale.getpreferredencoding()
        result = subprocess.run(command, check=True, capture_output=True, encoding=system_encoding, errors='replace', cwd=input_dir)
        print("Transcription successful.")
        
        json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
        if json_files:
            generated_json = os.path.join(input_dir, json_files[0])
            print(f"JSON file found: {generated_json}")
            
            try:
                with open(generated_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except UnicodeDecodeError:
                with open(generated_json, 'r', encoding=system_encoding) as f:
                    data = json.load(f)
            
            if 'params' in data:
                data['params']['translate'] = False
            
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"Modified JSON file saved: {output_json}")
        else:
            print(f"Warning: No JSON file found in {input_dir}")
            print("Folder contents:")
            print(os.listdir(input_dir))
    except subprocess.CalledProcessError as e:
        print(f"Error during transcription: {e}")
        print(f"Error output: {e.stderr}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def process_json(input_json, output_json):
    try:
        with open(input_json, 'r') as file:
            data = json.load(file)
        
        if 'transcription' in data:
            full_text = ' '.join(item['text'].strip() for item in data['transcription'])
            data['full_transcription'] = full_text
        
        with open(output_json, 'w') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        print(f"JSON processed and saved in {output_json}")
    except Exception as e:
        print(f"Error while processing JSON: {e}")

def main():
    for directory in [INPUT_DIR, OUTPUT_DIR, TEMP_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Folder created: {directory}")

    for filename in os.listdir(INPUT_DIR):
        if filename.endswith(('.wav', '.mp3', '.m4a')):
            input_path = os.path.join(INPUT_DIR, filename)
            temp_wav = os.path.join(TEMP_DIR, f"{os.path.splitext(filename)[0]}_16khz.wav")
            output_json = os.path.join(OUTPUT_DIR, f"{os.path.splitext(filename)[0]}.json")

            print(f"Processing {filename}...")
            
            convert_audio(input_path, temp_wav)
            
            if os.path.exists(temp_wav):
                transcribe_file(temp_wav, output_json)
                
                if os.path.exists(output_json):
                    process_json(output_json, output_json)
                
                os.remove(temp_wav)
            else:
                print(f"Error: Temporary file {temp_wav} was not created.")

            print(f"Processing completed for {filename}")

if __name__ == "__main__":
    main()