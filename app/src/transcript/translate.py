import json
import os
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast, GenerationConfig


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
INPUT_DIR = os.path.join(BASE_DIR, "audio_clips")
OUTPUT_DIR = os.path.join(BASE_DIR, "json")
TEMP_DIR = os.path.join(BASE_DIR, "tmp")

MODEL_DIR = os.path.join(BASE_DIR, "local_mbart_model")
TOKENIZER_DIR = os.path.join(BASE_DIR, "local_mbart_tokenizer")

if not os.path.exists(MODEL_DIR) or not os.path.exists(TOKENIZER_DIR):
    print("Local model not found. Downloading model...")
    from transformers import MBartForConditionalGeneration, MBart50TokenizerFast
    model = MBartForConditionalGeneration.from_pretrained('facebook/mbart-large-50-many-to-many-mmt')
    tokenizer = MBart50TokenizerFast.from_pretrained('facebook/mbart-large-50-many-to-many-mmt')
    model.save_pretrained(MODEL_DIR)
    tokenizer.save_pretrained(TOKENIZER_DIR)
    print("Model downloaded and saved locally.")

model = MBartForConditionalGeneration.from_pretrained(MODEL_DIR)
tokenizer = MBart50TokenizerFast.from_pretrained(TOKENIZER_DIR)

generation_config = GenerationConfig.from_model_config(model.config)
generation_config.max_length = 200
generation_config.early_stopping = True
generation_config.num_beams = 5
generation_config.forced_eos_token_id = 2

def translate_to_english(text, src_lang):
    try:
        lang_mapping = {
            'zh': 'zh_CN', 'ja': 'ja_XX', 'ko': 'ko_KR', 'vi': 'vi_VN', 'id': 'id_ID',
            'th': 'th_TH', 'ms': 'ms_MY', 'ar': 'ar_AR', 'tr': 'tr_TR', 'ru': 'ru_RU',
            'de': 'de_DE', 'nl': 'nl_XX', 'sv': 'sv_SE', 'it': 'it_IT', 'fr': 'fr_XX',
            'es': 'es_XX', 'pt': 'pt_XX', 'hi': 'hi_IN', 'ta': 'ta_IN', 'ur': 'ur_PK',
            'fa': 'fa_IR', 'ne': 'ne_NP', 'si': 'si_LK', 'en': 'en_XX'
        }
        
        src_lang = lang_mapping.get(src_lang, src_lang)
        tokenizer.src_lang = src_lang
        
        encoded = tokenizer(text, return_tensors="pt")
        generated_tokens = model.generate(
            **encoded, 
            forced_bos_token_id=tokenizer.lang_code_to_id["en_XX"],
            generation_config=generation_config
        )
        translated_text = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
        
        if not all(ord(char) < 128 for char in translated_text):
            print(f"Warning: Translation may not be in English. Source language: {src_lang}")
        
        return translated_text
    except Exception as e:
        print(f"Error during translation: {e}")
        return text

def process_json_file(input_json):
    try:
        with open(input_json, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        language = data['result']['language']
        
        if 'transcription' in data:
            full_text = ' '.join(item['text'].strip() for item in data['transcription'])
            
            if language != 'en':
                translated_text = translate_to_english(full_text, language)
                if not all(ord(char) < 128 for char in translated_text):
                    print(f"Warning: Translation for {input_json} may not be in English. Skipping.")
                    return
                data['result']['translated_text'] = translated_text
            else:
                data['result']['translated_text'] = full_text
        
        with open(input_json, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        
        print(f"Processing completed for {input_json}")
    except Exception as e:
        print(f"Error processing {input_json}: {e}")

def main():
    for directory in [INPUT_DIR, OUTPUT_DIR, TEMP_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Folder created: {directory}")

    for filename in os.listdir(OUTPUT_DIR):
        if filename.endswith('.json'):
            input_json = os.path.join(OUTPUT_DIR, filename)
            process_json_file(input_json)

if __name__ == "__main__":
    main()