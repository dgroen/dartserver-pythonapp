#!/usr/bin/env python3
"""
Test script to demonstrate SSL error handling

This script simulates HTTP requests to an HTTPS server to verify
that the SSL error handling works correctly.
"""

import socket
import time


def check_http_to_https_connection(host="127.0.0.1", port=5000, num_requests=5):
    """
    Send HTTP requests to an HTTPS server to trigger SSL errors

    Args:
        host: Server hostname (default: "127.0.0.1")
        port: Server port (default: 5000)
        num_requests: Number of requests to send (default: 5)
    """
    print("=" * 80)
    print("SSL Error Handling Test")
    print("=" * 80)
    print(f"Sending {num_requests} HTTP requests to HTTPS server at {host}:{port}")
    print("Expected: Server should handle errors gracefully without stack traces")
    print("=" * 80)
    print("")

    for i in range(num_requests):
        try:
            # Create a plain HTTP connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((host, port))

            # Send an HTTP request (not HTTPS)
            request = f"GET / HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n"
            sock.send(request.encode())

            # Try to receive response (will fail due to SSL error)
            try:
                _ = sock.recv(1024)
                print(f"Request {i+1}: Unexpected response received")
            except TimeoutError:
                print(f"Request {i+1}: Connection timeout (expected)")
            except Exception as e:
                print(f"Request {i+1}: Error - {type(e).__name__}")

            sock.close()

        except ConnectionRefusedError:
            print(f"Request {i+1}: Connection refused - is the server running?")
            break
        except Exception as e:
            print(f"Request {i+1}: Failed - {type(e).__name__}: {e}")

        # Small delay between requests
        if i < num_requests - 1:
            time.sleep(0.5)

    print("")
    print("=" * 80)
    print("Test complete!")
    print("Check the server console for SSL error messages.")
    print("You should see a single concise message instead of multiple stack traces.")
    print("=" * 80)


if __name__ == "__main__":
    import sys

    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    num_requests = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    check_http_to_https_connection(host, port, num_requests)
