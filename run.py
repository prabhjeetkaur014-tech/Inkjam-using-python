"""
inkJam Main Application Launcher.
Coordinates Flask backend, Tkinter desktop administration console,
and Data Analytics pipeline.
"""
import sys
import os
import time
import threading
import webbrowser

from app import app
from database import db
from analytics import generate_all_charts, export_data_to_csv

def start_server(port=5000):
    print(f" [Server] Starting inkJam Python Web Backend at http://localhost:{port}")
    # Run Flask server
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def main():
    args = sys.argv[1:]
    
    # Pre-generate visual assets
    print(" [Setup] Initializing charts with Matplotlib & Seaborn...")
    generate_all_charts()

    if "--server" in args:
        start_server()
        return

    if "--gui" in args:
        print(" [GUI] Launching inkJam Admin Console (Tkinter & Pillow)...")
        from admin_gui import launch_admin_gui
        launch_admin_gui()
        return

    if "--analytics" in args:
        print(" [Analytics] Generating data science reports & charts...")
        generate_all_charts()
        print("Done. Charts saved to img/charts/")
        return

    if "--export" in args:
        print(" [Export] Exporting database tables to CSV with Pandas...")
        folder = export_data_to_csv()
        print(f"Exported files to: {folder}")
        return

    # Default: Start backend server in a background thread and launch GUI / browser
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    time.sleep(1.0)
    print(" [Web] inkJam Web Application is live at http://localhost:5000")

    # If --web is requested, just open web app and wait
    if "--web" in args:
        webbrowser.open("http://localhost:5000")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down server.")
            return

    # Otherwise launch Tkinter Desktop Console by default
    try:
        print(" [GUI] Launching inkJam Tkinter Desktop App...")
        from admin_gui import launch_admin_gui
        # Also open web browser
        webbrowser.open("http://localhost:5000")
        launch_admin_gui()
    except Exception as e:
        print(f"Note: Running in console mode ({e}). Opening web browser...")
        webbrowser.open("http://localhost:5000")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down.")

if __name__ == "__main__":
    main()
