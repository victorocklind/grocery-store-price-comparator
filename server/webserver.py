# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
from database import Database
#import time
import cgi

database = Database()
hostName = "localhost"
serverPort = 8080

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        assert self.command == "GET"
        attrs = vars(self)
        for item in attrs.items():
            print("%s: %s" % item)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        file = open("website/"+self.path)
        file_content = file.read()
        if self.path == "/adminview.html":
            file_content = file_content.replace("ADD_THINGS_HERE", 
            " ".join([database.getProductString(l) for l in database.getProductDataForAdmin()]))
        self.wfile.write(bytes(file_content,'utf-8'))
        #self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
        #self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
        #self.wfile.write(bytes("<body>", "utf-8"))
        #self.wfile.write(bytes("<p>This is an example web server.</p>", "utf-8"))
        #self.wfile.write(bytes("</body></html>", "utf-8"))
        
    #TODO
    def do_POST(self):
        assert self.command == "POST"
        self.send_response(200) 
        self.send_header("Location", "/adminview.html")
        self.end_headers()

        #print all request data
        attrs = vars(self)
        for item in attrs.items():
            print("%s: %s" % item)

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'}
        )
        print("--------FORM----------")
        attrs = vars(form)
        for item in attrs.items():
            print("%s: %s" % item)
        #print form.getvalue("foo")
        #print form.getvalue("bin")
        #self.wfile.write("<html><body><h1>POST Request Received!</h1></body></html>")

if __name__ == "__main__":        
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
