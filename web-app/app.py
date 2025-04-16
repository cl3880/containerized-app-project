"""
Flask app for Object Recognizer

This app allows users to capture images using a webcam. A separate ML client
analyzes the image to identify the fruit and provides a text-based definition using the Merriam-Webster API.

The system could be further extended to provide audio feedback on the classification,
making it accessible to visually impaired users or educational settings.
"""

import base64
import os
import time
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union

import pymongo
import requests
from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    Response,
)
from pymongo.errors import PyMongoError
from pymongo.database import Database
from bson.objectid import ObjectId

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MW_API_URL = os.getenv("MW_URL", "https://dictionaryapi.com/api/v3/references/collegiate/json")
MW_API_KEY = os.getenv("MW_API_KEY")

load_dotenv()
app = Flask(__name__)

def setup_database() -> Optional[Database]:
    """Set up and return MongoDB database connection."""
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        logger.error("MONGODB_URI environment variable not set")
        return None
    
    try:
        client = pymongo.MongoClient(mongo_uri)
        db = client.get_database()
        client.admin.command("ping")
        logger.info("Connected to MongoDB")
        return db
    except PyMongoError as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return None


db = setup_database()


def clean_name(name: str) -> str:
    """Extract the first word from the classification name and clean it."""
    name = re.sub(r"\s*\d+\s*$", "", name)
    return name.strip().split()[0]


def parse_definition_text(text: str) -> Optional[str]:
    """Parse definition text and extract meaningful sentences."""
    text = re.sub(r"\{[^}]+\}", "", text).strip()
    sentences = [s.strip() for s in re.split(r"\.\s*", text) if s.strip()]
    
    if len(sentences) >= 2:
        return sentences[1] + "."
    elif sentences:
        return sentences[0] + "."
    return None


def extract_text_from_content(content: Union[str, List, Dict]) -> List[str]:
    """Recursively extract text content from API response structures."""
    parts = []
    
    if isinstance(content, str):
        parts.append(content)
    elif isinstance(content, list):
        for item in content:
            parts.extend(extract_text_from_content(item))
    elif isinstance(content, dict) and "t" in content:
        parts.append(content["t"])
        
    return parts


def extract_complete_definition(entry: Dict) -> str:
    """Extract a complete definition from the MW API response."""
    if not entry or "def" not in entry:
        return "No definition available."
    
    for sense in entry.get("def", []):
        for group in sense.get("sseq", []):
            for sense_entry in group:
                if not (isinstance(sense_entry, list) and len(sense_entry) >= 2):
                    continue
                    
                dt_items = sense_entry[1].get("dt", [])
                all_text_parts = []
                
                for item in dt_items:
                    if isinstance(item, list) and len(item) >= 2:
                        content = item[1]
                        all_text_parts.extend(extract_text_from_content(content))
                
                if all_text_parts:
                    text = " ".join(all_text_parts)
                    parsed_definition = parse_definition_text(text)
                    if parsed_definition:
                        return parsed_definition
    
    return "No definition available."


def get_definition(word: str) -> str:
    """
    Get a definition for the word using Merriam-Webster's Collegiate Dictionary API.
    """
    if not MW_API_KEY:
        logger.error("MW_API_KEY not configured")
        return "API key not configured."
    
    url = f"{MW_API_URL}/{word}?key={MW_API_KEY}"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            logger.warning(f"API error for word '{word}': {response.status_code}")
            return f"API error: {response.status_code}"
            
        data = response.json()
        if not data or not isinstance(data, list):
            logger.info(f"No results found for word '{word}'")
            return "No results found."
        
        first_entry = data[0]
        if not isinstance(first_entry, dict):
            logger.warning(f"Invalid API response format for word '{word}'")
            return "Invalid API response format."
            
        return extract_complete_definition(first_entry)
    except requests.RequestException as e:
        logger.error(f"Request error when fetching definition for '{word}': {e}")
        return "Network error while fetching definition."
    except Exception as e:
        logger.error(f"Error fetching definition for '{word}': {e}")
        return "Error processing definition."


def process_entry(entry: Dict) -> Dict:
    """Process and enhance an image classification entry."""
    classifications = entry.get("classifications", [])
    
    if not classifications:
        entry.update({
            "top_class": "Unknown",
            "definition": "No definition available.",
            "confidence": "0%"
        })
        return entry
    
    top_class, conf = classifications[0]
    clean_class = clean_name(top_class)
    definition = get_definition(clean_class)
    
    if db is not None:
        db.images.update_one(
            {"_id": entry["_id"]},
            {"$set": {"definition": definition}},
        )
    
    entry.update({
        "top_class": clean_class,
        "definition": definition,
        "confidence": f"{conf * 100:.2f}%"
    })
    
    return entry


@app.template_filter("timestamp_to_datetime")
def timestamp_to_datetime(timestamp: int) -> str:
    """Convert Unix timestamp to formatted date string."""
    return datetime.fromtimestamp(timestamp).strftime("%I:%M %p, %b %d")


@app.route("/")
def home():
    """Render home page with processed images."""
    if db is None:
        logger.error("Database connection not available")
        return "Database connection error", 500
        
    processed_entries = db.images.find({"status": "processed"}).sort("processed_at", -1)
    entries = [process_entry(entry) for entry in processed_entries]
    return render_template("index.html", entries=entries)


@app.route("/image/<image_id>")
def find_image(image_id: str):
    """Find and return an image from MongoDB by its ID."""
    if db is None:
        return "Database connection error", 500
        
    try:
        image_doc = db.images.find_one({"_id": ObjectId(image_id)})
        if image_doc and "image_data" in image_doc:
            return Response(image_doc["image_data"], mimetype="image/jpeg")
        return "Image not found", 404
    except Exception as e:
        print(f"Error serving image: {e}")
        return "Error serving image", 500


@app.route("/status")
def check_status():
    """Check if there are any pending images and return status."""
    if db is None:
        return jsonify({"error": "Database connection error"}), 500
        
    pending_count = db.images.count_documents({"status": "pending"})
    return jsonify({"pending": pending_count > 0})


@app.route("/upload", methods=["POST"])
def upload():
    """Process uploaded image and store it in DB."""
    if db is None:
        logger.error("Database connection not available during upload")
        return jsonify({"success": False, "message": "Database connection error"}), 500
        
    data = request.get_json()
    if not data or "image" not in data:
        logger.warning("Upload attempt with no image data")
        return jsonify({"success": False, "message": "No image data provided"}), 400
        
    try:
        _header, encoded = data["image"].split(",", 1)
    except (TypeError, KeyError, ValueError) as e:
        logger.warning(f"Invalid image data format: {e}")
        return jsonify({"success": False, "message": "Invalid image data"}), 400

    try:
        binary = base64.b64decode(encoded)
    except Exception as e:
        logger.error(f"Failed to decode base64 image: {e}")
        return jsonify({"success": False, "message": "Invalid image encoding"}), 400
        
    timestamp = int(time.time())
    formatted_time = datetime.fromtimestamp(timestamp).strftime("%I:%M %p")
    
    try:
        image_doc = {
            "timestamp": timestamp,
            "formatted_time": formatted_time,
            "image_data": binary,
            "status": "pending",
        }
        result = db.images.insert_one(image_doc)
        logger.info(f"Image uploaded successfully. ID: {result.inserted_id}")
        return jsonify({
            "success": True,
            "message": "Image uploaded successfully and is being processed.",
            "image_id": str(result.inserted_id),
        })
    except pymongo.errors.PyMongoError as e:
        logger.error(f"Error storing image in MongoDB: {e}")
        return jsonify({"success": False, "message": "Database error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)