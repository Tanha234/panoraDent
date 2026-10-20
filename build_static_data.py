"""
Build static dataset files (dataset.js and dataset.json) for DentAI Viewer.
This allows the viewer to run 100% statically without needing any backend server.
Works with VS Code Live Server, any static server, or directly in browser (file://).
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SPLITS = ['train', 'valid', 'test']
EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

CLASS_NAMES = [
    'Attrition', 'Cyst', 'Dental Caries',
    'Endodontically Treated Tooth', 'Impacted Third Molar',
    'Missing Tooth', 'Periapical Abnormality', 'Periapical Lesion',
    'Periodontal Pocket', 'Retained Root', 'Tooth Fracture'
]

def build_dataset():
    dataset = {}
    total_imgs = 0
    total_boxes = 0

    for split in SPLITS:
        img_dir = os.path.join(BASE_DIR, split, 'images')
        lbl_dir = os.path.join(BASE_DIR, split, 'labels')

        if not os.path.isdir(img_dir):
            dataset[split] = {'images': [], 'labels': {}}
            continue

        files = sorted(
            f for f in os.listdir(img_dir)
            if os.path.splitext(f)[1].lower() in EXTS
        )
        total_imgs += len(files)

        labels = {}
        for f in files:
            stem = os.path.splitext(f)[0]
            lpath = os.path.join(lbl_dir, stem + '.txt')
            boxes = []
            if os.path.exists(lpath):
                with open(lpath, 'r', encoding='utf-8') as fp:
                    for line in fp:
                        parts = line.strip().split()
                        if len(parts) == 5:
                            boxes.append([
                                int(parts[0]),
                                round(float(parts[1]), 5),
                                round(float(parts[2]), 5),
                                round(float(parts[3]), 5),
                                round(float(parts[4]), 5)
                            ])
                            total_boxes += 1
            if boxes:
                labels[f] = boxes

        dataset[split] = {
            'images': files,
            'labels': labels
        }
        print(f"[{split}] {len(files)} images, {len(labels)} labeled")

    # 1. Write dataset.js (for direct script tag inclusion, bypasses all CORS / local file restrictions)
    js_path = os.path.join(BASE_DIR, 'dataset.js')
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write('/* DentAI Auto-Generated Static Dataset */\n')
        f.write('window.DATASET = ' + json.dumps(dataset, separators=(',', ':')) + ';\n')

    # 2. Write dataset.json (for fetch API)
    json_path = os.path.join(BASE_DIR, 'dataset.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, separators=(',', ':'))

    print(f"\nSuccessfully generated:")
    print(f"  - dataset.js   ({os.path.getsize(js_path)/1024:.1f} KB)")
    print(f"  - dataset.json ({os.path.getsize(json_path)/1024:.1f} KB)")
    print(f"Total: {total_imgs} images, {total_boxes} bounding boxes.")

if __name__ == '__main__':
    build_dataset()
