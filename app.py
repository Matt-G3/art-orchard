from flask import Flask
from flask import Flask, request, redirect, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

class Image():


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

@app.route('/get-image/<id>')
def get_image(id):
    return send_from_directory('/static/uploads/', id)

@app.route('/upload_image/<id>', methods=['POST'])
def upload_image(id):
    if 'image' not in request.files:
        return "No file part", 400

    file = request.files['image']

    if file.filename == '':
        return 'No selected file', 400

    if file:
        filename = id
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        print(f"successful file upload: ID = {id}")
        return "File successfully uploaded!", 200