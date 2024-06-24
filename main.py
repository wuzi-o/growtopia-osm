
import argparse
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from ssl import PROTOCOL_TLS_SERVER, SSLContext
import requests
import requests_cache
import asyncio
import httpx
from diskcache import Cache

# Setup requests-cache for synchronous requests
requests_cache.install_cache('sync_cache', expire_after=3600)  # Cache expires after 1 hour

# Setup diskcache for asynchronous requests
async_cache = Cache('async_cache')  # Create a persistent cache on disk

class CachingHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        url = self.path[1:]  # Remove leading '/'
        if url.startswith("http"):
            # Handle as a proxy request
            response = requests.get(url)
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response.content)
        else:
            # Handle as a file request
            super().do_GET()

async def get_html_content(url: str, timeout: int = 10) -> str:
    # Check if the URL is already in the cache
    if url in async_cache:
        print(f'Using cached content for {url}')
        return str(async_cache[url])

    print(f'Making a new request for {url}')

    # If not in the cache, make a new request and store in the cache
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url)
        html = str(response.text)
        async_cache[url] = html
        return html

def main():
    host = "0.0.0.0"
    port = 8443
    ssl_context = SSLContext(PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')
    server = HTTPServer((host, port), CachingHTTPRequestHandler)
    server.socket = ssl_context.wrap_socket(server.socket, server_side=True)
    webbrowser.open(f"https://{host}:{port}/")
    server.serve_forever()

if __name__ == "__main__":
    main()