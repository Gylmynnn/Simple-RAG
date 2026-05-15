#!/usr/bin/env python3
"""
Web Runner for RAG Chatbot Flask Application.

PURPOSE / TUJUAN:
- EN: Entry point for running the Flask web server with proper initialization and error handling.
- ID: Entry point untuk menjalankan web server Flask dengan inisialisasi dan penanganan error yang tepat.

USAGE / PENGGUNAAN:
    python run_web.py                    # Run with defaults (localhost:5000)
    python run_web.py --host 0.0.0.0    # Run on all interfaces
    python run_web.py --port 8000       # Run on port 8000
    python run_web.py --no-debug        # Run in production mode
"""

import sys
import argparse
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from web.app import app, initialize_rag_system


def main():
    """
    Main entry point for Flask development server.
    
    PURPOSE / TUJUAN:
    - EN: Initializes RAG system and starts Flask development server with configurable options.
    - ID: Menginisialisasi sistem RAG dan memulai server pengembangan Flask dengan opsi yang dapat dikonfigurasi.
    """
    parser = argparse.ArgumentParser(
        description='RAG Chatbot Web Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python run_web.py                      # Run on localhost:5000 (debug mode)
  python run_web.py --host 0.0.0.0      # Run on all interfaces
  python run_web.py --port 8080          # Run on port 8080
  python run_web.py --no-debug           # Run in production mode
        '''
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to bind to (default: 5000)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        default=True,
        help='Enable debug mode (default: True)'
    )
    
    parser.add_argument(
        '--no-debug',
        action='store_true',
        help='Disable debug mode (production mode)'
    )
    
    parser.add_argument(
        '--threaded',
        action='store_true',
        default=True,
        help='Enable threaded mode (default: True)'
    )
    
    args = parser.parse_args()
    
    # Override debug if --no-debug is specified
    debug = args.debug and not args.no_debug
    
    try:
        print("=" * 60)
        print("RAG Chatbot Web Server")
        print("=" * 60)
        print(f"[web] Initializing RAG system...")
        
        # Initialize RAG system
        initialize_rag_system()
        
        print(f"[web] RAG system initialized successfully!")
        print(f"[web] Starting Flask server...")
        print("-" * 60)
        print(f"[web] Host: {args.host}")
        print(f"[web] Port: {args.port}")
        print(f"[web] Debug: {debug}")
        print(f"[web] Threaded: {args.threaded}")
        print("-" * 60)
        print(f"[web] Open your browser: http://{args.host}:{args.port}")
        print(f"[web] Press Ctrl+C to stop the server")
        print("=" * 60)
        print()
        
        # Start Flask development server
        app.run(
            host=args.host,
            port=args.port,
            debug=debug,
            threaded=args.threaded,
            use_reloader=debug
        )
        
    except KeyboardInterrupt:
        print("\n[web] Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[web] Error starting server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
