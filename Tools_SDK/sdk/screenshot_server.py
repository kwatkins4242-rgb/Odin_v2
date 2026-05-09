from flask import Flask, jsonify
import subprocess, os
from datetime import datetime

app = Flask(__name__)
SAVE_DIR = r"C:\AI\MyOdin\M2\screenshots_"

@app.route("/screenshot", methods=["POST", "GET"])
def take_screenshot():
    os.makedirs(SAVE_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(SAVE_DIR, f"screen_{timestamp}.png")
    try:
        result = subprocess.run(
            ["python", r"C:\AI\MyOdin\sdk\vision_tool.py", "--output", output_path],
            capture_output=True, text=True, timeout=30
        )
        return jsonify({"success": True, "path": output_path, "stdout": result.stdout, "stderr": result.stderr})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    print("Screenshot server running on http://localhost:9001")
    app.run(host="127.0.0.1", port=9001)