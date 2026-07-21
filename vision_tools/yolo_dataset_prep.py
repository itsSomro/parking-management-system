import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from sklearn.model_selection import train_test_split


DATASET_ROOT = r"C:\Users\SOHAM\PycharmProjects\ParkingSpaces\Datasets - LicensePlates"
OUTPUT_DIR = r"C:\Users\SOHAM\PycharmProjects\ParkingSpaces\yolo_dataset"

folders = ["images/train", "images/test",
           "labels/train", "labels/test"]

for folder in folders:
    os.makedirs(os.path.join(OUTPUT_DIR, folder), exist_ok=True)


# 2. DEFINE HELPER FUNCTIONS
def convert_xml_to_yolo(xml_path, txt_path):
    # Extracts bounding box from XML and converts to YOLO math format
    tree = ET.parse(xml_path)
    root = tree.getroot()

    size = root.find('size')
    w_img = float(size.find('width').text)
    h_img = float(size.find('height').text)

    with open(txt_path, 'w') as f:
        for obj in root.findall('object'):
            class_id = 0

            xmlbox = obj.find('bndbox')
            xmin = float(xmlbox.find('xmin').text)
            xmax = float(xmlbox.find('xmax').text)
            ymin = float(xmlbox.find('ymin').text)
            ymax = float(xmlbox.find('ymax').text)

            x_center = ((xmin + xmax) / 2) / w_img
            y_center = ((ymin + ymax) / 2) / h_img
            width = (xmax - xmin) / w_img
            height = (ymax - ymin) / h_img

            f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")


def process_data(pairs, subset_name):
    # Copies images and generates YOLO txt files for a specific dataset split
    print(f"Processing {subset_name} set ({len(pairs)} files)...")
    for img_path, xml_path in pairs:
        img_name = img_path.name
        txt_name = xml_path.stem + ".txt"

        out_img_path = os.path.join(OUTPUT_DIR, "images", subset_name, img_name)
        out_txt_path = os.path.join(OUTPUT_DIR, "labels", subset_name, txt_name)

        shutil.copy(img_path, out_img_path)
        convert_xml_to_yolo(xml_path, out_txt_path)


if __name__ == "__main__":
    print("Scanning folders for Images and XMLs...")
    dataset_path = Path(DATASET_ROOT)
    valid_pairs = []

    for xml_file in dataset_path.rglob("*.xml"):
        image_file = None
        for img_ext in ['.jpg', '.jpeg', '.png']:
            possible_image = xml_file.with_suffix(img_ext)
            if possible_image.exists():
                image_file = possible_image
                break

        if image_file:
            valid_pairs.append((image_file, xml_file))

    print(f"Found {len(valid_pairs)} valid Image+XML pairs.")

    if len(valid_pairs) == 0:
        print("[!] No pairs found! Check your DATASET_ROOT path.")
        exit()

    print("Shuffling and splitting data 80/20...")
    train_pairs, test_pairs = train_test_split(valid_pairs, test_size=0.20, random_state=42)

    process_data(train_pairs, "train")
    process_data(test_pairs, "test")

    print("Dataset successfully prepared! Check your yolo_dataset folder.")