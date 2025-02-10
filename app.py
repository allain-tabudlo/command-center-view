from flask import Flask, render_template, request, redirect, flash, jsonify, session
import mysql.connector
from datetime import datetime

import json


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database connection function
def connect_to_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="playerlocationtest",
        port=3307
    )

@app.route("/")
def home():
    return render_template("map.html")


@app.route('/replay')
def replay():
    return render_template('replay.html')

from flask import Flask, jsonify, request
import mysql.connector
import time


@app.route('/get-latest-player-data', methods=['GET'])
def get_latest_player_data():
    """Fetch the latest player location updates"""
    try:
        db_conn = connect_to_db()
        cursor = db_conn.cursor(dictionary=True)

        query = """
        SELECT 
            p.player_id, 
            p.name AS player_name, 
            p.rank AS player_rank,  
            p.unit AS player_unit, 
            p.DSG AS player_DSG, 
            ps.amo_used, 
            ps.hits_delivered, 
            pl.speed,
            pl.player_latitude, 
            pl.player_longitude, 
            pl.loc_timestamp
        FROM player_location pl
        INNER JOIN (
            SELECT player_id, MAX(loc_timestamp) AS latest_time
            FROM player_location
            GROUP BY player_id
        ) latest_loc ON pl.player_id = latest_loc.player_id
        INNER JOIN player p ON pl.player_id = p.player_id
        LEFT JOIN player_status ps ON pl.player_id = ps.player_id
        """

        cursor.execute(query)
        latest_players = cursor.fetchall()

        cursor.close()
        db_conn.close()
        return jsonify(latest_players)

    except Exception as e:
        print(f"Error in /get-latest-player-data: {e}")
        return jsonify({"error": str(e)}), 500




@app.route('/get-player-data', methods=['GET'])
def get_player_data():
    try:
        db_conn = connect_to_db()
        cursor = db_conn.cursor(dictionary=True)

        query = """
        SELECT 
            p.player_id, 
            p.name AS player_name, 
            p.rank AS player_rank,  
            p.unit AS player_unit, 
            p.DSG AS player_DSG, 
            ps.amo_used, 
            ps.hits_delivered, 
            pl.speed,
            pl.player_latitude, 
            pl.player_longitude, 
            pl.loc_timestamp
        FROM player_location pl
        INNER JOIN (
            SELECT player_id, MAX(loc_timestamp) AS latest_time
            FROM player_location
            GROUP BY player_id
        ) latest_loc ON pl.player_id = latest_loc.player_id
        INNER JOIN player p ON pl.player_id = p.player_id
        LEFT JOIN player_status ps ON pl.player_id = ps.player_id
        """

        cursor.execute(query)
        players = cursor.fetchall()
        cursor.close()
        db_conn.close()


        return jsonify(players)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500



@app.route('/update-player', methods=['POST'])
def update_player():
    """Updates only the player's location and speed"""
    data = request.json
    player_id = data.get('player_id')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    speed = data.get('speed', 20) 
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not player_id or not latitude or not longitude:
        return jsonify({"error": "Missing player_id, latitude, or longitude"}), 400

    db_conn = connect_to_db()
    cursor = db_conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO player_location (player_id, player_latitude, player_longitude, speed, loc_timestamp) VALUES (%s, %s, %s, %s, %s)",
            (player_id, latitude, longitude, speed, timestamp)
        )

        db_conn.commit()
        return jsonify({"message": "Player location updated successfully!"})
    except mysql.connector.Error as err:
        db_conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        db_conn.close()

@app.route('/get-player-history', methods=['GET'])
def get_player_history():
    player_id = request.args.get('player_id')
    if not player_id:
        return jsonify({"error": "player_id is required"}), 400

    try:
        db_conn = connect_to_db()
        cursor = db_conn.cursor(dictionary=True)

        query = """
        SELECT player_latitude AS latitude, player_longitude AS longitude, loc_timestamp AS timestamp
        FROM player_location
        WHERE player_id = %s
        ORDER BY loc_timestamp ASC
        """
        cursor.execute(query, (player_id,))
        history = cursor.fetchall()

        cursor.close()
        db_conn.close()
        return jsonify(history)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    
@app.route('/get-all-player-history', methods=['GET'])
def get_all_player_history():
    try:
        db_conn = connect_to_db()
        cursor = db_conn.cursor(dictionary=True)

        # Fetch player location data
        player_query = """
        SELECT pl.player_id, p.name AS player_name, p.rank AS player_rank, p.unit AS player_unit, 
               p.DSG as player_DSG, pl.player_latitude AS latitude, 
               pl.player_longitude AS longitude, pl.loc_timestamp AS timestamp,
               pl.speed, 
               COALESCE(ps.amo_used, 0) AS amo_used,
               COALESCE(ps.hits_delivered, 0) AS hits_delivered,
               'player' AS type, NULL AS marker_type, NULL AS name, NULL AS radius, NULL AS color, NULL AS geometry
        FROM player_location pl
        INNER JOIN player p ON pl.player_id = p.player_id
        LEFT JOIN player_status ps ON pl.player_id = ps.player_id
        """

        # Fetch special marker data
        marker_query = """
        SELECT NULL AS player_id, NULL AS player_name, NULL AS player_rank, NULL AS player_unit, 
               NULL as player_DSG, lat AS latitude, 
               lng AS longitude, timestamp, NULL AS speed, 
               NULL AS amo_used, NULL AS hits_delivered,
               'marker' AS type, type AS marker_type, NULL AS name, NULL AS radius, NULL AS color, NULL AS geometry
        FROM specialMarker
        """

        # Fetch custom marker data
        custom_marker_query = """
        SELECT NULL AS player_id, name AS player_name, NULL AS player_rank, NULL AS player_unit, 
               NULL as player_DSG, lat AS latitude, 
               lng AS longitude, timestamp, NULL AS speed, 
               NULL AS amo_used, NULL AS hits_delivered,
               'custom' AS type, NULL AS marker_type, name, radius, color, NULL AS geometry
        FROM custom_marker
        """

        # Fetch custom drawing data
        custom_drawing_query = """
        SELECT NULL AS player_id, NULL AS player_name, NULL AS player_rank, NULL AS player_unit, 
               NULL as player_DSG, NULL AS latitude, NULL AS longitude, timestamp, 
               NULL AS speed, NULL AS amo_used, NULL AS hits_delivered,
               'drawing' AS type, NULL AS marker_type, name, NULL AS radius, color, geometry
        FROM custom_drawings
        """

        # Combine all queries and sort by timestamp
        combined_query = f"""
        ({player_query}) 
        UNION ALL 
        ({marker_query}) 
        UNION ALL 
        ({custom_marker_query}) 
        UNION ALL 
        ({custom_drawing_query}) 
        ORDER BY timestamp ASC
        """

        cursor.execute(combined_query)
        history = cursor.fetchall()

        # Convert stored JSON string back to dictionary for geometry field
        for item in history:
            if item["geometry"]:
                item["geometry"] = json.loads(item["geometry"])

        cursor.close()
        db_conn.close()
        return jsonify(history)

    except Exception as e:
        print(f"Error in /get-all-player-history: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/save-special-marker', methods=['POST'])
def save_special_marker():
    try:
        data = request.json
        print(f"Received data: {data}")

        # Extract data
        marker_type = data.get('type')
        lat = data.get('lat')
        lng = data.get('lng')

        # Validate required fields
        if not all([marker_type, lat, lng]):
            print("Error: Missing required fields!")
            return jsonify({"error": "Missing required fields"}), 400

        # Save the marker to the database
        db_conn = connect_to_db()
        cursor = db_conn.cursor()

        query = """
        INSERT INTO specialMarker (type, lat, lng)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (marker_type, lat, lng))
        db_conn.commit()

        cursor.close()
        db_conn.close()

        return jsonify({"message": "Marker saved successfully!"}), 200

    except Exception as e:
        print(f"Error saving marker: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

    
@app.route('/get-special-markers', methods=['GET'])
def get_special_markers():
    try:
        db_conn = connect_to_db()
        cursor = db_conn.cursor(dictionary=True)

        query = "SELECT id, type, lat, lng, timestamp FROM specialMarker"
        cursor.execute(query)
        markers = cursor.fetchall()

        cursor.close()
        db_conn.close()
        return jsonify(markers)

    except Exception as e:
        print(f"Error fetching special markers: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/save-custom-marker', methods=['POST'])
def save_custom_marker():
    try:
        data = request.json
        print(f"Received data: {data}")  

        # Extracting fields
        marker_type = data.get('type')
        name = data.get('name')
        radius = data.get('radius')
        color = data.get('color')
        lat = data.get('lat')
        lng = data.get('lng')

        # Ensure no missing fields
        if not all([marker_type, name, radius, color, lat, lng]):
            print("Error: Missing required fields!")  # Debugging
            return jsonify({"error": "Missing required fields"}), 400

        # Database connection
        db_conn = connect_to_db()
        cursor = db_conn.cursor()

        query = """
        INSERT INTO custom_marker (type, name, radius, color, lat, lng, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        cursor.execute(query, (marker_type, name, radius, color, lat, lng))
        db_conn.commit()

        cursor.close()
        db_conn.close()

        return jsonify({"message": "Custom marker saved successfully!"}), 200

    except Exception as e:
        print(f"Error saving custom marker: {e}")  
        return jsonify({"error": str(e)}), 500  # Return detailed error message

@app.route('/get-custom-markers', methods=['GET'])
def get_custom_markers():
    try:
        db_conn = connect_to_db()
        cursor = db_conn.cursor(dictionary=True)

        query = "SELECT id, name, radius, color, lat, lng FROM custom_marker"
        cursor.execute(query)
        markers = cursor.fetchall()

        cursor.close()
        db_conn.close()
        return jsonify(markers)

    except Exception as e:
        print(f"Error fetching custom markers: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    
@app.route('/save-custom-drawing', methods=['POST'])
def save_custom_drawing():
    try:
        data = request.json
        name = data.get('name')
        color = data.get('color')
        geometry = data.get('geometry')

        if not all([name, color, geometry]):
            return jsonify({"error": "Missing required fields"}), 400

        db_conn = connect_to_db()
        cursor = db_conn.cursor()

        query = """
        INSERT INTO custom_drawings (name, color, geometry, timestamp)
        VALUES (%s, %s, %s, NOW())
        """
        cursor.execute(query, (name, color, json.dumps(geometry)))
        db_conn.commit()
        cursor.close()
        db_conn.close()

        return jsonify({"message": "Custom drawing saved!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


    
@app.route('/get-custom-drawings', methods=['GET'])
def get_custom_drawings():
    try:
        db_conn = connect_to_db()
        cursor = db_conn.cursor(dictionary=True)

        query = "SELECT name, color, geometry FROM custom_drawings"
        cursor.execute(query)
        drawings = cursor.fetchall()

        cursor.close()
        db_conn.close()

        # Convert stored JSON string back to dictionary
        for drawing in drawings:
            drawing['geometry'] = json.loads(drawing['geometry'])

        return jsonify(drawings), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)
