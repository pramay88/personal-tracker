# tracker-app/backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os
MONGO_URI = "mongodb+srv://pramaywankhade7:<db_password>@cluster0.pkgjiul.mongodb.net/"

client = MongoClient(os.environ.get("MONGO_URI"))

app = Flask(__name__)
CORS(app)


db = client["tracker"]
users = db["users"]
tasks = db["tasks"]


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    if users.find_one({"username": data["username"]}):
        return jsonify({"error": "User exists"}), 400
    # Create new user
    user_id = users.insert_one({"username": data["username"], "password": data["password"]}).inserted_id
    # Insert tasks (only for the new user)
    for i in range(1, 4):  # Adjust task count to 3 tasks
        tasks.insert_one({"user_id": user_id, "task_name": f"Task {i}", "history": {}})
    return jsonify({"message": "User registered"})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = users.find_one({"username": data["username"], "password": data["password"]})
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({"user_id": str(user["_id"])})

@app.route("/get_tasks", methods=["GET"])
def get_tasks():
    user_id = request.args.get("user_id")
    user_tasks = list(tasks.find({"user_id": ObjectId(user_id)}))
    for task in user_tasks:
        task["_id"] = str(task["_id"])
        task["user_id"] = str(task["user_id"])
    return jsonify(user_tasks)

@app.route("/update_task", methods=["POST"])
def update_task():
    data = request.json
    task = tasks.find_one({"user_id": ObjectId(data["user_id"]), "task_name": data["task_name"]})
    if not task:
        return jsonify({"error": "Task not found"}), 404
    task["history"][data["date"]] = data["status"]
    tasks.update_one({"_id": task["_id"]}, {"$set": {"history": task["history"]}})
    return jsonify({"message": "Task updated"})

if __name__ == "__main__":
    app.run(debug=True)