import json
import re
import sys
from pathlib import Path


import paho.mqtt.client as mqtt
# MQTT broker settings
BROKER = "192.168.1.146"   # replace with broker IP/hostname
PORT = 1883                           # 8883 if using TLS
TOPIC = "dogs/adoption/updates"
CLIENT_ID = "dogrescue_publisher"

# Authentication
USERNAME = "wombat"
PASSWORD = "wombat"


def publish_message(message: str):
    # Create client
    client = mqtt.Client(client_id=CLIENT_ID)

    # Set username and password
    client.username_pw_set(USERNAME, PASSWORD)

    # Connect to broker
    client.connect(BROKER, PORT, 60)

    # Publish message
    result = client.publish(TOPIC, message)

    # Check if publish was successful
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"✅ Message sent to {TOPIC}: {message}")
    else:
        print("❌ Failed to publish message")

    # Disconnect
    client.disconnect()


# -----------------------------
# Validation helper functions
# -----------------------------

AGE_PATTERN = re.compile(r"^(About\s+)?\d+\s+(year|years|yo|year old|years old|month|months|week|weeks)($|.*)", re.IGNORECASE)
COLOUR_PATTERN = re.compile(r"^(?=.*\S).+$")



def valid_age(age: str) -> bool:
    if not isinstance(age, str):
        return False
    return bool(AGE_PATTERN.match(age.strip()))


def valid_colour(colour: str) -> bool:
    if not isinstance(colour, str):
        return False
    return bool(COLOUR_PATTERN.match(colour.strip()))


def validate_image_paths(dog, base_path: Path) -> list[str]:
    errors = []

    main_image = dog.get("image", "")
    images_list = dog.get("images", [])

    def check_one(path_str, field_label):
        img_path = base_path / path_str
        if not img_path.exists():
            errors.append(f"Missing image file for {field_label}: {img_path}")

    if isinstance(main_image, str) and main_image.strip():
        check_one(main_image, "image")

    if isinstance(images_list, list):
        for idx, img in enumerate(images_list):
            if isinstance(img, str) and img.strip():
                check_one(img, f"images[{idx}]")

    return errors


# -----------------------------
# Main validation logic
# -----------------------------

def validate_dogs(json_path: str, min_count: int, images_base_dir: str) -> None:
    path = Path(json_path)
    base_path = Path(images_base_dir)

    if not path.exists():
        print(f"ERROR: File not found: {json_path}")
        sys.exit(1)

    if not base_path.exists():
        print(f"ERROR: Image base directory not found: {images_base_dir}")
        sys.exit(1)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        sys.exit(1)

    # --- Rule 1: Minimum count ---
    if not isinstance(data, list):
        print("ERROR: JSON must be a list of dog entries.")
        sys.exit(1)

    if len(data) < min_count:
        print(f"ERROR: Expected at least {min_count} entries, found {len(data)}.")
        sys.exit(1)

    errors = []
    required_fields = ["name", "nameext", "image"]

    # --- Rule 6: No duplicate nameext values ---
    nameext_seen = {}
    for i, dog in enumerate(data):
        nx = dog.get("nameext")
        if isinstance(nx, str) and nx.strip():
            if nx in nameext_seen:
                errors.append(
                    f"Duplicate nameext '{nx}' found in entries {nameext_seen[nx]} and {i}"
                )
            else:
                nameext_seen[nx] = i
        else:
            errors.append(f"Entry {i} missing or empty 'nameext' (also required for dedupe check)")

    # --- Validate each dog entry ---
    for i, dog in enumerate(data):
        prefix = f"Entry {i} ({dog.get('name','<no name>')}):"

        # Rule 2 — required fields
        for field in required_fields:
            v = dog.get(field)
            if not isinstance(v, str) or not v.strip():
                errors.append(f"{prefix} missing or empty field '{field}'")

        # Rule 3 — age format
        age = dog.get("age")
        if age and not valid_age(age):
            errors.append(f"{prefix} invalid age format: '{age}'")

        # Rule 4 — colour format
        colour = dog.get("colour")
        if colour and not valid_colour(colour):
            errors.append(f"{prefix} invalid colour format: '{colour}' (expected comma-separated words)")

        # Rule 5 — image existence
        img_errors = validate_image_paths(dog, base_path)
        errors.extend([f"{prefix} {e}" for e in img_errors])

    # --- Final report ---
    if errors:
        errstr = ""
        print("ERROR: Validation failed:")
        for e in errors:
            print(" -", e)
            errstr += e


        publish_message(errstr)

        sys.exit(1)

    print("SUCCESS: Validation passed.")


# -----------------------------
# CLI wrapper
# -----------------------------

def main():
    if len(sys.argv) != 4:
        print("Usage: python validate_dogs.py <json_file> <min_count> <images_base_dir>")
        sys.exit(1)

    json_file = sys.argv[1]
    try:
        min_count = int(sys.argv[2])
    except ValueError:
        print("ERROR: min_count must be an integer.")
        sys.exit(1)

    images_base_dir = sys.argv[3]

    validate_dogs(json_file, min_count, images_base_dir)


if __name__ == "__main__":
    main()
