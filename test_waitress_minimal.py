from waitress import serve

def simple_app(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return [b"Hello World"]

if __name__ == "__main__":
    print("Starting minimal Waitress app...")
    try:
        serve(simple_app, host='127.0.0.1', port=5020)
    except Exception as e:
        print(f"Waitress error: {e}")
