import os
import signal
import http.server
import socketserver
from UploadParser import UploadParser
from MultiUploadParser import MultiUploadParser
from Filler import Filler
import hashlib
import datetime
import os.path
from pathlib import Path
import sys

PORT=9080
if len(sys.argv)>=2:
    PORT=int(sys.argv[1])

UPLOAD_DIR=os.path.join(os.environ['HOME'],'uploads')
if len(sys.argv)>=3:
    UPLOAD_DIR=sys.argv[2]

SCRIPT_DIR=os.path.dirname(os.path.realpath(__file__))


if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
  def do_GET(self):
    if self.path[0:3]=='/f/':
        self.send_response(200)
        self.send_header('Content-type','text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(bytes(Filler(self.path).html(),"utf-8"))
    elif self.path=='/q':
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Server stopped")
        # Start a new thread to shutdown the server
        import threading
        threading.Thread(target=self.server.shutdown).start() 
    else:
        super().do_GET()
  def do_POST(self):
    print(f"{self.command=}")
    print(f"{self.client_address=}")
    print(f"{self.requestline=}")
    print(f"{self.path=}")
    print(f"{self.headers.is_multipart()=}")
    # print(f"{self.headers.get_payload()=}")
    # print(f"{self.headers.as_string()=}")
    # for k,v in self.headers.items():
    #   print(f"{k} : {v}")
    contenttype=self.headers.get("content-type")
    contentlength=int(self.headers.get("content-length"))
    print(f"{contenttype=}")
    print(f"{contentlength=}")
    c=contenttype.split(';')
    boundary=None
    if c[0]=="multipart/form-data":
      print(f"{c[1]=}")
      BH='boundary='
      try:
        i=c[1].index(BH)
        boundary=c[1][(i+len(BH)):]
      except ValueError:
        pass
    print(f"{boundary=}")

    # debug
    if self.path == '/dump.html':
        body=self.rfile.read(contentlength)
        file = tempfile.NamedTemporaryFile(dir=UPLOAD_DIR,prefix="body",delete=False)
        file.write(body)
        file.close()
        self.send_response(200)
        self.send_header('Content-type','text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(bytes("Saved body to %s"%os.basename(file.name),"utf-8"))

    elif self.path == '/upload.html':
        prs=UploadParser(boundary, UPLOAD_DIR)
        prs.parse(self.rfile,contentlength)
        self.send_response(200)
        self.send_header('Content-type','text/plain; charset=utf-8')
        self.end_headers()
        # self.wfile.write(bytes(("POST request saved to %s"%file.name),'utf8'))
        if prs.receivedFrom == None:
            self.wfile.write(bytes("Data discarded","ascii"))
        else:
            self.wfile.write(bytes((
                ("POST request complete.\r\n"
                "Written %d/%d bytes\r\n"
                "file %s\r\n"
                "sha256 %s\r\n"
                "saved as %s\r\n"
                )%(
                    prs.receivedSize,
                    contentlength,
                    prs.receivedOriginalFileName,
                    prs.receivedSha256,
                    prs.receivedDataName)),'utf8'))
    elif self.path == '/multiupload.html':
        prs=MultiUploadParser(boundary,UPLOAD_DIR)
        prs.parse(self.rfile,contentlength)
        self.send_response(200)
        self.send_header('Content-type','text/plain; charset=utf-8')
        self.end_headers()
        # self.wfile.write(bytes(("POST request saved to %s"%file.name),'utf8'))
        if prs.receivedFrom == None:
            self.wfile.write(bytes("Data discarded","ascii"))
        else:
            enc='utf8'
            self.wfile.write(bytes("POST request complete.\r\nReceived %d bytes\r\n"%contentlength,enc))
            for fi in prs.receivedDataInfo:
                self.wfile.write(bytes((
                    ("Written %d bytes\r\n"
                    "file %s\r\n"
                    "sha256 %s\r\n"
                    "saved as %s\r\n"
                    )%(
                        fi.size,
                        fi.originalName,
                        fi.sha256,
                        os.path.basename(fi.tempName))),enc))

    else:
        pass
    return

with socketserver.TCPServer(("",PORT),MyHttpRequestHandler) as httpd:
  #def signal_handler(sig, frame):
  #    signal.signal(signal.SIGINT, signal.SIG_DFL)
  #    print('Shutting down server...')
  #    httpd.shutdown()
  #    print('Server shutdown complete')
  #signal.signal(signal.SIGINT, signal_handler)
  # signal.signal(signal.SIGTERM, signal_handler)
  print("serving at port ",PORT)
  try:
    httpd.serve_forever()
  except KeyboardInterrupt:
    print("Keyboard interrupt")
    pass
  finally:
    httpd.server_close()
    print('Server stopped')

