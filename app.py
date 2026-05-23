from flask import Flask, request, send_from_directory, jsonify
import os
import uuid
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)



def load_data():
    with open('data.json', 'r') as file:
        return json.load(file)

def save_data(data):
    with open("data.json", "w") as file:
        json.dump(data, file)

@app.route('/')
def hello_world():
    return 'App is working'

@app.route('/get-image/<id>')
def get_image(id):
    # assumes png uploads (we’ll improve later if needed)
    filename = f"{id}.png"
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/upload_image/<parent_id>', methods=['POST'])
def upload_image(parent_id):

    if 'image' not in request.files:
        return "No file part", 400

    imageFile = request.files['image']

    if imageFile.filename == '':
        return 'No selected file', 400

    if imageFile:
        # generate unique ID
        image_id = str(uuid.uuid4())

        filename = f"{image_id}.png"
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        imageFile.save(path)

        return jsonify({
            "message": "File successfully uploaded!",
            "id": image_id,
            "url": f"/get-image/{image_id}"
        }), 200

    return "File not uploaded", 400

@app.route('/test')
def test():
    # generates a fake upload ID to prove system is working
    test_id = str(uuid.uuid4())

    return jsonify({
        "status": "ok",
        "generated_uuid": test_id,
        "note": "UUID generation working correctly"
    })
