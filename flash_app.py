from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, abort, Response
from flask_caching import Cache
import requests
from script import set_api_key, generate_character
import json
import threading
import uuid
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

def get_image_url(session_id):
    image_url_path = f'/home/GiovanniPanda/mysite/static/image_url_{session_id}.json'

    if not os.path.exists(image_url_path):
        return None

    with open(image_url_path, 'r') as f:
        data = json.load(f)

    return data.get('image_url')

def delete_files(session_id):
    params_path = f'/home/GiovanniPanda/mysite/static/Params_{session_id}.json'
    image_url_path = f'/home/GiovanniPanda/mysite/static/image_url_{session_id}.json'

    if os.path.exists(params_path):
        os.remove(params_path)
    else:
        print(f"{params_path} not found")

    if os.path.exists(image_url_path):
        os.remove(image_url_path)
    else:
        print(f"{image_url_path} not found")

def generate_character_wrapper(description, model, update_progress, cache, session_id):
    result = generate_character(description, model, lambda value: update_progress(value, session_id), cache, session_id)
    if result is False:
        cache.set(f'{session_id}_generation_error', True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        api_key = request.form.get('api_key')
        set_api_key(api_key)

        return redirect(url_for('generating'))

    return render_template('index.html')

@app.route('/generate_character', methods=['POST'])
def generate_character_request():
    data = request.get_json()

    api_key = data.get('api_key')
    description = data.get('description')
    model = data.get('model')
    session_id = request.cookies.get('session_id')

    def update_progress(value, session_id):
        cache.set(f'{session_id}_progress', value)
        print(f"Progress: {value}")


    set_api_key(api_key)
    cache.set('progress', 0)

    # Create a new thread to run the generate_character function
    generate_thread = threading.Thread(target=generate_character_wrapper, args=(description, model, update_progress, cache, session_id))
    generate_thread.start()

    cache.set('generation_complete', False)  # Set the generation status as incomplete

    return jsonify(success=True)

@app.route('/test_progress')
def test_progress():
    return render_template('test_progress.html')

@app.route('/delete_files/<session_id>')
def delete_files_route(session_id):
    delete_files(session_id)
    return jsonify({"success": True})

@app.route('/generating')
def generating():
    session_id = str(uuid.uuid4())  # Generate a new UUID for the session
    resp = make_response(render_template('generating.html'))
    resp.set_cookie('session_id', session_id)  # Set the session_id cookie
    return resp

@app.route('/display')
def display_character():
    session_id = request.cookies.get('session_id')
    image_url = get_image_url(session_id)
    return render_template('Character_Sheet.html', session_id=session_id, image_url=image_url)

@app.route('/download_image/<session_id>')
def download_image(session_id):
    image_url = request.args.get('url')
    if not image_url:
        abort(400, "Missing image URL")

    try:
        response = requests.get(image_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        abort(500, f"Error downloading image: {str(e)}")

    image_data = response.content
    content_type = response.headers.get('Content-Type', 'application/octet-stream')

    return Response(image_data, content_type=content_type)

@app.route('/delete_temp_image/<session_id>')
def delete_temp_image(session_id):
    temp_image_file = f'/home/GiovanniPanda/mysite/static/temp_image_{session_id}.png'
    if os.path.exists(temp_image_file):
        os.remove(temp_image_file)
        return jsonify({'result': 'success'})
    else:
        return jsonify({'result': 'error', 'message': 'File not found'})


@app.route('/progress')
def get_progress():
    session_id = request.cookies.get('session_id')
    progress = cache.get(f'{session_id}_progress') or 0
    print(f"get_progress() called. Session progress: {progress}")
    return jsonify({"progress": progress})

@app.route('/generation_status')
def generation_status():
    session_id = request.cookies.get('session_id')
    status = cache.get(f'{session_id}_generation_complete') or False
    error_occurred = cache.get(f'{session_id}_generation_error') or False
    api_exception_occurred = cache.get(f'{session_id}_api_exception') or False
    return jsonify({"complete": status, "error": error_occurred, "api_exception": api_exception_occurred})

@app.route('/done')
def done():
    return render_template('done.html')

@app.route('/error')
def error():
    return render_template('error.html')

@app.route('/api_exception')
def api_exception():
    return render_template('api_exception.html')