from flask import Flask, request, send_from_directory, jsonify
import os
import uuid
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads/')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DATA_FILE = 'data.json'

# -----------------------
# Data helpers
# -----------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Load into memory on startup
db = load_data()

# -----------------------
# Home route
# -----------------------
@app.route('/')
def hello_world():
    return 'App is working'

# -----------------------
# GET IMAGE (UUID-based)
# -----------------------
@app.route('/get-image/<id>')
def get_image(id):
    filename = f"{id}.png"
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# -----------------------
# GET all images for a parent
# -----------------------
@app.route('/images/<parent_id>', methods=['GET'])
def get_images_for_parent(parent_id):
    children = db.get(parent_id, [])
    return jsonify({
        "parent_id": parent_id,
        "images": children
    }), 200

@app.route('/base-images', methods=['GET'])
def get_base_images():
    return jsonify({
        "base_images": db.get("__base__", [])
    }), 200

@app.route('/upload_image', methods=['POST'])
@app.route('/upload_image/<parent_id>', methods=['POST'])
def upload_image(parent_id=None):
    if 'image' not in request.files:
        return "No file part", 400
    imageFile = request.files['image']
    if imageFile.filename == '':
        return 'No selected file', 400
    if imageFile:
        image_id = str(uuid.uuid4())
        filename = f"{image_id}.png"
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        imageFile.save(path)

        if parent_id is None:
            parent_id = "__base__"

        if parent_id not in db:
            db[parent_id] = []
        db[parent_id].append({
            "id": image_id,
            "url": f"/get-image/{image_id}"
        })
        save_data(db)
        return jsonify({
            "message": "File successfully uploaded!",
            "id": image_id,
            "url": f"/get-image/{image_id}",
            "parent_id": parent_id,
            "total_images": len(db[parent_id])
        }), 200
    return "File not uploaded", 400

@app.route('/delete_image/<parent_id>/<image_id>', methods=['DELETE'])
def delete_image(parent_id, image_id):
    if parent_id not in db:
        return jsonify({"error": "Parent not found"}), 404

    original_count = len(db[parent_id])
    db[parent_id] = [img for img in db[parent_id] if img["id"] != image_id]

    if len(db[parent_id]) == original_count:
        return jsonify({"error": "Image not found under this parent"}), 404

    # Remove file from disk
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{image_id}.png")
    if os.path.exists(filepath):
        os.remove(filepath)

    save_data(db)
    return jsonify({"message": "Image deleted", "remaining": len(db[parent_id])}), 200



@app.route('/test')
def test():
    return jsonify({
        "status": "ok",
        "generated_uuid": str(uuid.uuid4()),
        "tracked_parents": len(db),
        "total_images": sum(len(v) for v in db.values())
    })