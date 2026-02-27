"""
app.py — Flask entry point for the Real Estate Marketing AI Agent.

Routes:
    GET  /               — serves the frontend (index.html)
    POST /search-amenities — SSE stream of agent activity + final results
    POST /generate-copy  — generates marketing copy from amenities
"""

import os
import json
from flask import Flask, request, jsonify, send_from_directory, Response
from dotenv import load_dotenv

from agent import run_agent_streaming
from services.copy_generator import generate_marketing_copy

# Load environment variables from .env
load_dotenv()

# Serve frontend/ as static files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")


@app.route("/")
def serve_frontend():
    """Serve index.html at the root URL."""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/search-amenities", methods=["POST"])
def search_amenities():
    """
    Accept a property address + optional buyer profile and stream
    agent activity via Server-Sent Events (SSE).

    Each SSE event is a JSON object with:
        - type: "step" or "done"
        - node: planner / search / critic / done
        - message: human-readable step description
        - api_call_count: running total
        - (on "done"): coordinates, amenities, buyer_profile, agent_log
    """
    body = request.get_json(silent=True)

    if not body or "address" not in body:
        return jsonify({
            "error": "Missing required field: 'address'."
        }), 400

    address = body["address"].strip()
    if not address:
        return jsonify({"error": "The 'address' field must not be empty."}), 400

    profile_text = body.get("buyer_profile", "").strip()

    # If no buyer profile provided, use a default generic one
    if not profile_text:
        profile_text = "General buyer looking for a well-connected neighbourhood with everyday amenities."

    def generate_sse():
        """Generator that yields SSE events as the agent runs."""
        try:
            for update in run_agent_streaming(address, profile_text):
                if update.get("is_done"):
                    # Final event with full results
                    event_data = {
                        "type": "done",
                        "node": "done",
                        "coordinates": update.get("coordinates"),
                        "amenities": update.get("amenities", {}),
                        "buyer_profile": update.get("buyer_profile"),
                        "agent_log": update.get("agent_log", []),
                        "api_call_count": update.get("api_call_count", 0),
                    }
                else:
                    # Progress event
                    log_entry = update.get("log_entry", {})
                    event_data = {
                        "type": "step",
                        "node": update.get("node", ""),
                        "message": log_entry.get("message", "") if log_entry else "",
                        "iteration": log_entry.get("iteration", 0) if log_entry else 0,
                        "api_call_count": update.get("api_call_count", 0),
                    }

                yield f"data: {json.dumps(event_data)}\n\n"

        except Exception as e:
            error_data = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"

    return Response(
        generate_sse(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/generate-copy", methods=["POST"])
def generate_copy():
    """
    Accept a property address and selected amenities, and return AI-generated marketing copy.

    Request:  { "address": "1 Raffles Place, Singapore", "selected_amenities": {...} }
    Response: { "marketing_copy": "..." }
    """

    body = request.get_json(silent=True)

    if not body or "address" not in body or "selected_amenities" not in body:
        return jsonify({
            "error": "Missing required fields: 'address' or 'selected_amenities'."
        }), 400

    address = body["address"].strip()
    selected_amenities = body["selected_amenities"]
    
    if not address:
        return jsonify({"error": "The 'address' field must not be empty."}), 400

    # Generate marketing copy
    try:
        buyer_profile_data = body.get("buyer_profile")
        marketing_copy = generate_marketing_copy(
            address,
            selected_amenities,
            buyer_profile_data=buyer_profile_data
        )
    except Exception as e:
        return jsonify({"error": f"Copy generation failed: {str(e)}"}), 500

    # Return final response
    return jsonify({
        "marketing_copy": marketing_copy,
    })


if __name__ == "__main__":
    print("\n  Real Estate Marketing AI Agent")
    print("  Open http://127.0.0.1:5000 in your browser")
    print("  API /search-amenities  http://127.0.0.1:5000/search-amenities")
    print("  API /generate-copy     http://127.0.0.1:5000/generate-copy\n")
    app.run(debug=True)
