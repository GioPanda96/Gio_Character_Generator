import openai
import json
import os
import re
import requests
from concurrent.futures import ThreadPoolExecutor, TimeoutError

openai.api_key = None

def set_api_key(key):
    api_key = key
    openai.api_key = api_key

def fix_common_json_errors(json_str):
    try:
        json.loads(json_str)
        return json_str
    except json.decoder.JSONDecodeError:
        # Remove comments (single-line only)
        json_str = re.sub(r'\s*//.*$', '', json_str, flags=re.MULTILINE)

        # Escape unescaped quotes
        json_str = re.sub(r'(?<!\\)(?<!\\\")\"', r'\\"', json_str)

        # Remove any invalid control characters
        json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)

        # Remove backslashes before double quotes
        json_str = re.sub(r'\\\"', '\"', json_str)

        return json_str

def request_character_info(description, base_json_form, user_messages, section, base_json_form_with_comments, model):
    messages = [
        {"role": "system", "content": "You are a smart JSON character sheet generator for D&D 5e. You take a description of the character and a JSON file as input, you only return the filled out JSON file, nothing else. You can come up with any any information that's not given in the description according to D&D 5e rules, but it has to be included in the JSON file, never outside."},
    ] + user_messages + [
        {"role": "user", "content": f"Section {section}:\n{description}\n\nPlease fill out the following section of the JSON form, in detail:\n{base_json_form_with_comments}\n\nDo not provide the entire JSON file, just this section."},
    ]

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages
    )

    result = response.choices[0].message.content
    fixed_result = fix_common_json_errors(result.strip())

    try:
        parsed_result = json.loads(fixed_result)
    except json.decoder.JSONDecodeError as e:
        print(f"Error parsing fixed JSON output for section {section}:")
        print(fixed_result)
        raise e

    return parsed_result

def load_json_file_with_comments(file_name):
    with open(file_name, 'r') as file:
        json_content = file.read()
        return json_content

def is_valid_json(data):
    try:
        json.loads(json.dumps(data, indent=2))
        return True
    except ValueError:
        return False

def export_json_file(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file, indent=4)

def merge_dicts(dict1, dict2):
    result = dict1.copy()
    result.update(dict2)
    return result

def format_name(name):
    return " ".join(word for word in name.split("_"))

def generate_character(character_description, model, update_progress=None, cache=None, session_id=None):
    if not character_description:
        print("No description provided. Exiting the script.")
        return

    json_template_paths = [
        "/home/GiovanniPanda/mysite/JSON_Forms/stats.json",
        "/home/GiovanniPanda/mysite/JSON_Forms/proficiencies_and_equipment_3.5.json" if model == "gpt-3.5-turbo" else "/home/GiovanniPanda/mysite/JSON_Forms/proficiencies_and_equipment_4.json",
        "/home/GiovanniPanda/mysite/JSON_Forms/racial_traits_and_feats_3.5.json" if model == "gpt-3.5-turbo" else "/home/GiovanniPanda/mysite/JSON_Forms/racial_traits_and_feats_4.json",
        "/home/GiovanniPanda/mysite/JSON_Forms/spells_and_appearance.json",
        "/home/GiovanniPanda/mysite/JSON_Forms/affiliations,_descriptions_and_backstory_GPT-3.json" if model == "gpt-3.5-turbo" else "/home/GiovanniPanda/mysite/JSON_Forms/affiliations,_descriptions_and_backstory_GPT-4.json",
    ]

    output_file_name = f"/home/GiovanniPanda/mysite/static/Params_{session_id}.json"

    filled_character_sheet = {}
    user_messages = []

    try:
        for i, template_path in enumerate(json_template_paths, 1):
            base_json_form = load_json_file_with_comments(template_path)
            template_name = format_name(os.path.splitext(os.path.basename(template_path))[0])

            for attempt in range(3):
                success = False
                print(f"Generating {template_name} for your character. Attempt {attempt + 1}. Please wait...")
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(request_character_info, character_description, base_json_form, user_messages, i, base_json_form, model)
                    try:
                        part_filled_sheet = future.result(timeout=210)  # Set a 2-minute timeout
                        fixed_part_filled_sheet = json.loads(fix_common_json_errors(json.dumps(part_filled_sheet, indent=2)))
                        success = True
                    except TimeoutError:
                        print(f"The AI took too long to generate the character section on attempt {attempt + 1}.")
                    except json.JSONDecodeError:
                        print(f"Failed to generate a valid {template_name} section on attempt {attempt + 1}.")
                    except Exception as e:
                        print(f"An unexpected error occurred on attempt {attempt + 1}: {e}")

                    if success:
                        break

                if attempt == 2 and not success:
                    print("All attempts failed. Exiting...")
                    cache.set("generation_error", True)  # Set an error status in the cache
                    return False

            # Print the fixed filled character sheet information
            print(f"Section {i}:\n{json.dumps(fixed_part_filled_sheet, indent=2)}\n")

            # Merge the fixed filled character sheet information with the rest of the sheet
            filled_character_sheet = merge_dicts(filled_character_sheet, fixed_part_filled_sheet)

            # Update the user_messages with the fixed filled character sheet information
            user_messages.append({"role": "assistant", "content": json.dumps(fixed_part_filled_sheet, indent=2)})

            # Update the progress
            if update_progress:
                update_progress(i / len(json_template_paths))
                print(f"Progress: {i / len(json_template_paths)}")

        export_json_file(output_file_name, filled_character_sheet)

    except Exception as e:
        print(f"An error occurred: {e}")
        if "The model" in str(e) and "does not exist" in str(e):
            cache.set("api_exception", True)  # Set a specific error flag in the cache
        else:
            cache.set("generation_error", True)  # Set a general error flag in the cache
        return False



    with open(output_file_name) as json_file:
        params = json.load(json_file)
        race = params["race"]
        char_class = params["class"]
        appearance = params["appearance_AI"]

    prompt = f"D&D character portrait\nRace: {race}\nClass: {char_class}\nDescription: {appearance}"

    # Replace the existing image generation code with the new API call
    deepai_api_key = 'DEEPAI_KEY'
    response = requests.post(
        "https://api.deepai.org/api/fantasy-portrait-generator",
        data={
            'text': prompt,
            'grid_size': '1',  # Request a single image output
        },
        headers={'api-key': deepai_api_key}
    )

    response_data = response.json()

    # Print the entire response data for debugging
    print("API response data:", response_data)

    if 'output_url' in response_data:
        image_url = response_data['output_url']
        print("Image URL:", image_url)

        # Generate a JSON file with the image URL
        data = {'image_url': image_url}

        with open(f'/home/GiovanniPanda/mysite/static/image_url_{session_id}.json', 'w') as outfile:
            json.dump(data, outfile)

        cache.set(f'{session_id}_generation_complete', True)  # Set the generation status as complete

        return True
