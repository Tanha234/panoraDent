"""
DentAI Dataset Viewer - Optimized Flask Backend
Pre-caches image lists on startup and serves them efficiently.
"""

import os
import json
from flask import Flask, jsonify, send_file, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CLASS_NAMES = [
    'Attrition', 'Cyst', 'Dental Caries',
    'Endodontically Treated Tooth', 'Impacted Third Molar',
    'Missing Tooth', 'Periapical Abnormality', 'Periapical Lesion',
    'Periodontal Pocket', 'Retained Root', 'Tooth Fracture'
]

SPLITS = ['train', 'valid', 'test']
EXTS   = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

# ── Pre-cache everything on startup ──────────────────────────────────────────
IMAGE_CACHE = {}
LABEL_CACHE = {}

def preload_all():
    for split in SPLITS:
        img_dir   = os.path.join(BASE_DIR, split, 'images')
        label_dir = os.path.join(BASE_DIR, split, 'labels')

        if not os.path.isdir(img_dir):
            IMAGE_CACHE[split] = []
            LABEL_CACHE[split] = {}
            continue

        files = sorted(
            f for f in os.listdir(img_dir)
            if os.path.splitext(f)[1].lower() in EXTS
        )
        IMAGE_CACHE[split] = files
        print(f"  [{split}] {len(files)} images")

        # Pre-parse every label file
        labels = {}
        for f in files:
            stem = os.path.splitext(f)[0]
            lpath = os.path.join(label_dir, stem + '.txt')
            boxes = []
            if os.path.exists(lpath):
                with open(lpath, 'r') as fp:
                    for line in fp:
                        parts = line.strip().split()
                        if len(parts) == 5:
                            cid = int(parts[0])
                            boxes.append({
                                'class_id':   cid,
                                'class_name': CLASS_NAMES[cid] if cid < len(CLASS_NAMES) else f'Class {cid}',
                                'cx': float(parts[1]),
                                'cy': float(parts[2]),
                                'w':  float(parts[3]),
                                'h':  float(parts[4])
                            })
            labels[f] = boxes
        LABEL_CACHE[split] = labels

print("Pre-loading dataset…")
preload_all()
print("Ready!\n")

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    with open(os.path.join(BASE_DIR, 'viewer.html'), 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/api/images')
def api_images():
    split = request.args.get('split', 'train')
    if split not in SPLITS:
        return jsonify({'error': 'Invalid split'}), 400
    images = IMAGE_CACHE.get(split, [])
    return jsonify({'images': images, 'count': len(images)})

@app.route('/api/labels')
def api_labels():
    split = request.args.get('split', 'train')
    image = request.args.get('image', '')
    if split not in SPLITS:
        return jsonify({'error': 'Invalid split'}), 400
    boxes = LABEL_CACHE.get(split, {}).get(image, [])
    return jsonify({'boxes': boxes, 'count': len(boxes)})

# Return labels for a BATCH of images in one request (saves round-trips)
@app.route('/api/labels_batch', methods=['POST'])
def api_labels_batch():
    data  = request.get_json(force=True)
    split = data.get('split', 'train')
    names = data.get('images', [])
    if split not in SPLITS:
        return jsonify({'error': 'Invalid split'}), 400
    result = {n: LABEL_CACHE.get(split, {}).get(n, []) for n in names}
    return jsonify(result)

@app.route('/images/<split>/<path:filename>')
def serve_image(split, filename):
    if split not in SPLITS:
        return 'Not found', 404
    img_path = os.path.join(BASE_DIR, split, 'images', filename)
    if not os.path.exists(img_path):
        return 'Not found', 404
    return send_file(img_path, max_age=3600)   # browser cache for 1 hr

if __name__ == '__main__':
    print("=" * 50)
    print("  DentAI Viewer  ->  http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=False, port=5000, threaded=True)
