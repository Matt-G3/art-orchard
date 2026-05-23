from flask import Flask, request, send_from_directory, jsonify
import os
import uuid
import json

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
DATA_FILE = os.path.join(BASE_DIR, "data.json")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "base_images": [],
            "children": {}
        }

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    if "base_images" not in data:
        data["base_images"] = []

    if "children" not in data:
        data["children"] = {}

    return data


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


db = load_data()


@app.route("/")
def home():
    return "App is working"


@app.route("/test")
def test():
    return jsonify({
        "status": "ok",
        "base_images": len(db["base_images"]),
        "tracked_parents": len(db["children"]),
        "total_child_images": sum(len(v) for v in db["children"].values())
    })


@app.route("/get-image/<image_id>")
def get_image(image_id):
    filename = f"{image_id}.png"
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/base-images", methods=["GET"])
def get_base_images():
    return jsonify({
        "base_images": db["base_images"]
    }), 200


@app.route("/images/<parent_id>", methods=["GET"])
def get_images_for_parent(parent_id):
    children = db["children"].get(parent_id, [])

    return jsonify({
        "parent_id": parent_id,
        "images": children
    }), 200


@app.route("/upload_image", methods=["POST"])
@app.route("/upload_image/<parent_id>", methods=["POST"])
def upload_image(parent_id=None):
    if "image" not in request.files:
        return jsonify({"error": "No file part"}), 400

    image_file = request.files["image"]

    if image_file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    image_id = str(uuid.uuid4())
    filename = f"{image_id}.png"
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    image_file.save(path)

    image_data = {
        "id": image_id,
        "url": f"/get-image/{image_id}",
        "parent_id": parent_id
    }

    if parent_id is None:
        db["base_images"].append(image_data)
        image_type = "base"
    else:
        if parent_id not in db["children"]:
            db["children"][parent_id] = []

        db["children"][parent_id].append(image_data)
        image_type = "child"

    save_data(db)

    return jsonify({
        "message": "Image uploaded",
        "type": image_type,
        "id": image_id,
        "url": f"/get-image/{image_id}",
        "parent_id": parent_id
    }), 200


@app.route("/delete_image/<image_id>", methods=["DELETE"])
def delete_image(image_id):
    removed = False

    original_base_count = len(db["base_images"])
    db["base_images"] = [
        img for img in db["base_images"]
        if img["id"] != image_id
    ]

    if len(db["base_images"]) != original_base_count:
        removed = True

    for parent_id in list(db["children"].keys()):
        original_child_count = len(db["children"][parent_id])

        db["children"][parent_id] = [
            img for img in db["children"][parent_id]
            if img["id"] != image_id
        ]

        if len(db["children"][parent_id]) != original_child_count:
            removed = True

        if len(db["children"][parent_id]) == 0:
            del db["children"][parent_id]

    if not removed:
        return jsonify({"error": "Image not found"}), 404

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], f"{image_id}.png")

    if os.path.exists(filepath):
        os.remove(filepath)

    save_data(db)

    return jsonify({
        "message": "Image deleted",
        "id": image_id
    }), 200

@app.route("/tree/<root_id>", methods=["GET"])
def get_tree(root_id):

    def build_tree(image_id):

        children = db["children"].get(image_id, [])

        return {
            "id": image_id,
            "children": [
                build_tree(child["id"])
                for child in children
            ]
        }

    tree = build_tree(root_id)

    return jsonify(tree), 200

if __name__ == "__main__":
    app.run(debug=True)