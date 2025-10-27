from flask import Blueprint, jsonify

from config.database import get_connection

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    """Basic health check for the application."""
    return jsonify({"status": "ok"}), 200


@health_bp.route("/health/db", methods=["GET"])
def health_db():
    """Check database connectivity by opening a connection and running a trivial query.

    Returns 200 when DB is reachable and can execute a simple query, otherwise 500 with error details.
    """
    conn = get_connection()
    if not conn:
        return jsonify({"status": "error", "db": "unavailable"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return jsonify({"status": "ok", "db": "reachable"}), 200
    except Exception as e:
        return jsonify({"status": "error", "db": "query_failed", "error": str(e)}), 500
    finally:
        try:
            conn.close()
        except Exception:
            pass
