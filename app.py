#!flask/bin/python

# Author: Ngo Duy Khanh
# Email: ngokhanhit@gmail.com
# Git repository: https://github.com/ngoduykhanh/flask-file-uploader
# This work based on jQuery-File-Upload which can be found at https://github.com/blueimp/jQuery-File-Upload/

import os
import PIL
from PIL import Image
import simplejson
import traceback

from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename

from lib.upload_file import uploadfile

import json

app = Flask(__name__)

BLOCK_CONFIG_PATH = 'block_config.json'

DEFAULT_FIXED_EXTS = ["bat", "cmd", "com", "cpl", "exe", "scr", "js"]

def load_block_config():
    # 기본값 구조
    cfg = {
        "fixed": {ext: False for ext in DEFAULT_FIXED_EXTS},
        "custom": []
    }
    if not os.path.exists(BLOCK_CONFIG_PATH):
        return cfg

    with open(BLOCK_CONFIG_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # fixed
    if "fixed" in data:
        cfg["fixed"].update(data["fixed"])
    # custom
    if "custom" in data:
        cfg["custom"] = data["custom"]

    return cfg


def save_block_config(cfg):
    with open(BLOCK_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.config['SECRET_KEY'] = 'hard to guess string'
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'data')
app.config['THUMBNAIL_FOLDER'] = os.path.join(BASE_DIR, 'data', 'thumbnail')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['csv', 'txt', 'gif', 'png', 'jpg', 'jpeg', 'bmp', 'rar', 'zip', '7zip', 'doc', 'docx', 'xlsx', 'ppt', 'pptx', 'pdf', 'mp3', 'mp4', 'avi'])
IGNORED_FILES = set(['.gitignore'])

bootstrap = Bootstrap(app)


def allowed_file(filename):
    if '.' not in filename:
        return False

    ext = filename.rsplit('.', 1)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        return False

    # 차단 확장자도 서버에서 한 번 더 체크
    cfg = load_block_config()
    blocked_fixed = {e for e, v in cfg["fixed"].items() if v}
    blocked_custom = set(cfg["custom"])
    blocked = blocked_fixed | blocked_custom

    if ext in blocked:
        return False

    return True


def gen_file_name(filename):
    """
    If file was exist already, rename it and return a new name
    """

    i = 1
    while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        name, extension = os.path.splitext(filename)
        filename = '%s_%s%s' % (name, str(i), extension)
        i += 1

    return filename


def create_thumbnail(image):
    try:
        base_width = 80
        img = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], image))
        w_percent = (base_width / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((base_width, h_size), PIL.Image.ANTIALIAS)
        img.save(os.path.join(app.config['THUMBNAIL_FOLDER'], image))

        return True

    except:
        print(traceback.format_exc())
        return False


@app.route("/upload", methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        files = request.files['file']

        if files:
            filename = secure_filename(files.filename)
            filename = gen_file_name(filename)
            mime_type = files.content_type

            if not allowed_file(files.filename):
                result = uploadfile(name=filename, type=mime_type, size=0, not_allowed_msg="File type not allowed")

            else:
                # save file to disk
                uploaded_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                files.save(uploaded_file_path)

                # create thumbnail after saving
                if mime_type.startswith('image'):
                    create_thumbnail(filename)
                
                # get file size after saving
                size = os.path.getsize(uploaded_file_path)

                # return json for js call back
                result = uploadfile(name=filename, type=mime_type, size=size)
            
            return simplejson.dumps({"files": [result.get_file()]})

    if request.method == 'GET':
        # get all file in ./data directory
        files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'],f)) and f not in IGNORED_FILES ]
        
        file_display = []

        for f in files:
            size = os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], f))
            file_saved = uploadfile(name=f, size=size)
            file_display.append(file_saved.get_file())

        return simplejson.dumps({"files": file_display})

    return redirect(url_for('index'))


@app.route("/delete/<string:filename>", methods=['DELETE'])
def delete(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file_thumb_path = os.path.join(app.config['THUMBNAIL_FOLDER'], filename)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)

            if os.path.exists(file_thumb_path):
                os.remove(file_thumb_path)
            
            return simplejson.dumps({filename: 'True'})
        except:
            return simplejson.dumps({filename: 'False'})


# serve static files
@app.route("/thumbnail/<string:filename>", methods=['GET'])
def get_thumbnail(filename):
    return send_from_directory(app.config['THUMBNAIL_FOLDER'], filename=filename)


@app.route("/data/<string:filename>", methods=['GET'])
def get_file(filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER']), filename=filename)


@app.route('/', methods=['GET'])
def index():
    cfg = load_block_config()
    return render_template(
        'index.html',
        fixed_blocked=cfg["fixed"],     # {"bat": True, "cmd": False, ...}
        custom_blocked=cfg["custom"]    # ["sh", "php", ...]
    )

@app.route('/api/block/fixed', methods=['POST'])
def api_block_fixed():
    data = request.get_json() or {}
    ext = (data.get('ext') or '').lower()
    checked = bool(data.get('checked'))

    cfg = load_block_config()
    if ext not in cfg["fixed"]:
        return simplejson.dumps({"success": False, "error": "UNKNOWN_FIXED_EXT"})

    cfg["fixed"][ext] = checked
    save_block_config(cfg)

    return simplejson.dumps({"success": True})

@app.route('/api/block/custom', methods=['POST'])
def api_add_custom():
    data = request.get_json() or {}
    ext = (data.get('ext') or '').strip().lower()

    if ext.startswith('.'):
        ext = ext[1:]

    # 2-1. 최대 20자리
    if not ext or len(ext) > 20:
        return simplejson.dumps({"success": False, "error": "INVALID_LENGTH"})

    cfg = load_block_config()

    # 3-1. 최대 200개까지
    if len(cfg["custom"]) >= 200:
        return simplejson.dumps({"success": False, "error": "MAX_200"})

    # 중복 체크
    if ext in cfg["custom"]:
        return simplejson.dumps({"success": False, "error": "DUPLICATE"})

    cfg["custom"].append(ext)
    save_block_config(cfg)

    return simplejson.dumps({"success": True, "ext": ext})

@app.route('/api/block/custom/<string:ext>', methods=['DELETE'])
def api_delete_custom(ext):
    ext = ext.strip().lower()
    cfg = load_block_config()

    if ext in cfg["custom"]:
        cfg["custom"].remove(ext)
        save_block_config(cfg)

    return simplejson.dumps({"success": True})

if __name__ == '__main__':
    app.run(debug=True)
