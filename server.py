import os
import signal
import http.server
import socketserver
import tempfile
from FormDataParser import FormDataParser
import hashlib
import datetime
import os.path
from pathlib import Path

PORT=9080

UPLOAD_DIR=os.path.join(os.environ['HOME'],'uploads')
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

class UploadParser(FormDataParser):
    def __init__(self,boundary):
        super(UploadParser,self).__init__(boundary)
        self.count=0
        self.dgst=None
        self.receivedSha256='00'
        self.receivedOriginalFileName=''
        self.receivedDataName=''
        self.receivedSigName=''
        self.receivedSize=0
        self.receivedFrom=b''
        self.fieldClose=None
        self.fieldData=None

    def setup_field_data(self):
        self.tf=tempfile.NamedTemporaryFile(dir=UPLOAD_DIR, delete=False)
        self.dgst=hashlib.sha256()
        def data(self, buffer):
            self.dgst.update(buffer)
            self.tf.write(buffer)
        def close(self):
            # print("close_field_data")
            self.tf.close()
            self.receivedSha256=self.dgst.hexdigest()
            self.receivedOriginalFileName=self.fieldFileName.decode('utf-8')
            self.receivedDataName=self.tf.name
            self.receivedSize=self.count
        self.fieldClose=close
        self.fieldData=data
        print("c=%s,d=%s"%(self.fieldClose,self.fieldData))


    def setup_field_sig(self):
        self.tf=tempfile.NamedTemporaryFile(dir=UPLOAD_DIR, delete=False)
        def data(self, buffer):
            if self.count<=1024*16 :
                self.tf.write(buffer)
            else:
                print("too much data for %s, ignore"%self.fieldName)

        def close(self):
            self.tf.close()
            self.receivedSigName=self.tf.name
        self.fieldClose=close
        self.fieldData=data

    def setup_field_from(self):
        def data(self,buffer):
            take=len(buffer)
            if self.count>128:
                take=128-self.count
            if take>0:
                self.receivedFrom+=buffer[0:take]
            # print("append %d bytes to %s"%(take,self.fieldName))
                
        def close(self):
            self.receivedFrom=self.receivedFrom.decode("utf-8")
        self.fieldClose=close
        self.fieldData=data


    def processPartialFieldData(self,buffer):
        # print("received %d bytes for %s"%(len(buffer),self.fieldName))
        if len(buffer)==0: return
        self.count+=len(buffer)
        if self.fieldData != None:
            self.fieldData(self,buffer)
        else:
            print("WOx7VAedWye12lEde data processor is not defined")


    def finalizeHeaders(self):
        # print("received field %s",self.fieldName)
        if self.fieldName==b'data' : self.setup_field_data()
        elif self.fieldName==b'sig' : self.setup_field_sig()
        elif self.fieldName==b'from' : self.setup_field_from()
        else:
            self.fieldClose=None
            self.fieldClose=None
        self.count=0

    def finalizeField(self):
        print("finish field %s"%self.fieldName)
        if self.fieldClose!=None:
            self.fieldClose(self)
        else:
            print("W7M1838T3E7DKHzdQ no field closer")
        self.fieldClose=None
        self.fieldData=None

    def finalizeForm(self):
        os.rename(self.receivedSigName,self.receivedDataName+".shig")
        self.receivedDataName=os.path.basename(self.receivedDataName)
        with open(os.path.join(UPLOAD_DIR,"upload.log"),"a") as log:
            now=datetime.datetime.now()
            log.write("%s,%s,%s,%s,%d,%s\n"%(
                now.strftime("%Y-%m-%d %H:%M:%S"),
                self.receivedFrom,
                self.receivedDataName,
                self.receivedSha256,
                self.receivedSize,
                self.receivedOriginalFileName))
        
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
    if self.path == '/dump.html':
        body=self.rfile.read(contentlength)
        file = tempfile.NamedTemporaryFile(dir=UPLOAD_DIR,prefix="body",delete=False)
        file.write(body)
        file.close()
        self.send_response(200)
        self.send_header('Content-type','text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(bytes("Saved body to %s"%os.basename(file.name),"utf-8"))

    else:
        prs=UploadParser(boundary)
        prs.parse(self.rfile,contentlength)
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
                prs.receivedOriginalFileName,
                prs.receivedSha256,
                prs.receivedDataName)),'utf8'))
    return

with socketserver.TCPServer(("",PORT),MyHttpRequestHandler) as httpd:
  # def signal_handler(sig, frame):
  #     print('Shutting down server...')
  #     httpd.server_close()
  # signal.signal(signal.SIGINT, signal_handler)
  # signal.signal(signal.SIGTERM, signal_handler)
  print("serving at port ",PORT)
  httpd.serve_forever()

