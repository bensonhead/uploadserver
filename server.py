import os
import signal
import http.server
import socketserver
import tempfile
from FormDataParser import FormDataParser
import hashlib
import datetime
import os.path

PORT=9081

class UploadParser(FormDataParser):
    def __init__(self,boundary):
        super(UploadParser,self).__init__(boundary)
        self.count=0
        self.dgst=None
        self.receivedSha256='00'
        self.receivedFileName=''
        self.receivedDiskName=''
        self.receivedSize=0
        self.receivedExtra=b''
        self.fieldClose=None
        self.fieldData=None

    def setup_field_file(self):
        self.tf=tempfile.NamedTemporaryFile(dir=".", delete=False)
        self.dgst=hashlib.sha256()
        def data(self, buffer):
            print("received %d bytes for %s"%(len(buffer),self.fieldName))
            self.dgst.update(buffer)
            self.tf.write(buffer)
        def close(self):
            self.tf.close()
            self.receivedSha256=self.dgst.hexdigest()
            self.receivedFileName=self.fieldFileName.decode('utf-8')
            self.receivedDiskName=os.path.basename(self.tf.name)
            self.receivedSize=self.count
        self.fieldClose=close
        self.fieldData=data

    def setup_field_extra(self):
        def data(self,buffer):
            take=len(buffer)
            if self.count>128:
                take=128-self.count
            if take>0:
                self.receivedExtra+=buffer[0:take]
            # print("append %d bytes to %s"%(take,self.fieldName))
                
        def close(self):
            self.receivedExtra=self.receivedExtra.decode("utf-8")
        self.fieldClose=close
        self.fieldData=data


    def processPartialFieldData(self,buffer):
        if len(buffer)==0: return
        self.count+=len(buffer)
        if self.fieldData != None:
            self.fieldData(self,buffer)

    def finalizeHeaders(self):
        # print("received field %s",self.fieldName)
        if self.fieldName==b'file' : self.setup_field_file()
        elif self.fieldName==b'extra' : self.setup_field_extra()
        else:
            self.fieldClose=None
            self.fieldData=None
        self.count=0

    def finalizeField(self):
        if self.fieldClose!=None:
            self.fieldClose(self)
        self.fieldClose=None
        self.fieldData=None

    def finalizeForm(self):
        with open("upload.log","a") as log:
            now=datetime.datetime.now()
            log.write("%s,%s,%s,%s,%d,%s\n"%(
                now.strftime("%Y-%m-%d %H:%M:%S"),
                self.receivedDiskName,
                self.receivedExtra,
                self.receivedSha256,
                self.receivedSize,
                self.receivedFileName))
        
class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
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
    # body=self.rfile.read(contentlength)
    # file = tempfile.NamedTemporaryFile(dir=".",delete=False)
    # file.write(body)
    # file.close()
    prs=UploadParser(boundary)
    prs.parse(self.rfile,contentlength)
    prs.finalizeForm()

    self.send_response(200)
    self.send_header('Content-type','text/plain; charset=utf-8')
    self.end_headers()
    # self.wfile.write(bytes(("POST request saved to %s"%file.name),'utf8'))
    self.wfile.write(bytes((
        ("POST request complete.\r\n"
        "Written %d/%d bytes\r\n"
        "file %s\r\n"
        "sha256 %s\r\n"
        "saved as %s\r\n"
        )%(
            prs.receivedSize,
            contentlength,
            prs.receivedFileName,
            prs.receivedSha256,
            prs.receivedDiskName)),'utf8'))
    return

with socketserver.TCPServer(("",PORT),MyHttpRequestHandler) as httpd:
  # def signal_handler(sig, frame):
  #     print('Shutting down server...')
  #     httpd.server_close()
  # signal.signal(signal.SIGINT, signal_handler)
  # signal.signal(signal.SIGTERM, signal_handler)
  print("serving at port ",PORT)
  httpd.serve_forever()

