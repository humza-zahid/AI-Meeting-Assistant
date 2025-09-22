#!/usr/bin/env python3
"""
Simple HTTP server for Google Calendar Auth Frontend
Serves static files on port 8080
"""

import http.server
import socketserver
import os
import sys
from urllib.parse import urlparse

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with CORS support"""
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight OPTIONS requests"""
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests with proper routing"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Default to auth.html for root path
        if path == '/':
            path = '/auth.html'
        
        # Remove leading slash for file system
        if path.startswith('/'):
            path = path[1:]
        
        # Security check - prevent directory traversal
        if '..' in path or path.startswith('/'):
            self.send_error(403, "Forbidden")
            return
        
        # Check if file exists
        if not os.path.exists(path):
            # For SPA routing, serve auth.html for unknown routes
            if not path.endswith(('.html', '.css', '.js', '.ico', '.png', '.jpg', '.svg')):
                path = 'auth.html'
        
        # Set the path for the parent class
        self.path = '/' + path
        
        # Call parent implementation
        super().do_GET()
    
    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{self.log_date_time_string()}] {format % args}")

def main():
    """Start the HTTP server"""
    PORT = 8080
    
    # Change to the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print(f"🚀 Starting Google Calendar Auth Frontend Server")
    print(f"📁 Serving files from: {script_dir}")
    print(f"🌐 Server URL: http://localhost:{PORT}")
    print(f"🔐 Auth page: http://localhost:{PORT}/auth.html")
    print(f"")
    print(f"💡 Make sure your FastAPI backend is running on port 8000")
    print(f"   Start backend with: python backend.py")
    print(f"⚠️  Press Ctrl+C to stop the server")
    print(f"")
    
    try:
        with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped by user")
        sys.exit(0)
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is already in use!")
            print(f"💡 Try stopping any existing servers or use a different port")
        else:
            print(f"❌ Server error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
