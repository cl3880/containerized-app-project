import base64
import requests
import sys
import os

TEST_IMAGES = {
    "apple": "web-app/tests/test_data/apple.png",
    "banana": "web-app/tests/test_data/banana.jpg",
    "train_apple": "web-app/tests/sample_training_images/train_apple.jpg",
    "train_banana": "web-app/tests/sample_training_images/train_banana.jpg"
}

def upload_image(image_name: str):
    if image_name not in TEST_IMAGES:
        print(f"Unknown image '{image_name}'. Available options: {', '.join(TEST_IMAGES.keys())}")
        sys.exit(1)

    image_path = TEST_IMAGES[image_name]
    if not os.path.exists(image_path):
        print(f"Image file not found: {image_path}")
        sys.exit(1)

    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    
    data_uri = "data:image/jpeg;base64," + encoded
    payload = {"image": data_uri}
    url = "http://localhost:5001/upload"

    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response:", response.text)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m web-app.tests.test_upload <image_name>")
        sys.exit(1)

    upload_image(sys.argv[1])
