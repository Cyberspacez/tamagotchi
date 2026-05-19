from flask import Flask, jsonify, request

app = Flask(__name__)

# Knight state stored in memory
state = {
    "name": "Knight",
    "hunger": 10,
    "happiness": 10,
    "health": 10,
    "age": 0,
    "alive": True,
    "sleeping": False,
    "tiredness": 0,
    "outside": False,  # True = knight is in the browser world
    "food_collected": 0
}

# Pi calls this to push its current state to the server
@app.route("/push", methods=["POST"])
def push():
    data = request.json
    state.update(data)
    return jsonify({"ok": True})

# Browser calls this to get the knight's current state
@app.route("/state", methods=["GET"])
def get_state():
    return jsonify(state)

# Browser calls this when the knight goes outside
@app.route("/go_outside", methods=["POST"])
def go_outside():
    state["outside"] = True
    return jsonify({"ok": True})

# Browser calls this when the knight comes back with food
@app.route("/return", methods=["POST"])
def return_home():
    data = request.json
    state["outside"] = False
    state["food_collected"] = data.get("food_collected", 0)
    state["hunger"] = min(10, state["hunger"] + data.get("food_collected", 0))
    return jsonify({"ok": True})

# Pi polls this to check if knight is outside
@app.route("/is_outside", methods=["GET"])
def is_outside():
    return jsonify({"outside": state["outside"]})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)