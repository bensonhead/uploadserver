from FormDataParser import FormDataParser
import tempfile
import hashlib
import os
import datetime

class UploadParser(FormDataParser):
    def __init__(self,boundary, upload):
        super(UploadParser,self).__init__(boundary)
        self.UPLOAD_DIR=upload
        self.LOG="upload.log"
        self.count=0
        # to succeed, the form must contain these 3 fields
        self.receivedFrom=None
        self.receivedSigName=None
        self.receivedDataName=None
        self.dgst=None
        self.receivedSha256='00'
        self.receivedOriginalFileName=''
        self.receivedSize=0
        self.fieldClose=None
        self.fieldData=None

    def setup_field_data(self):
        self.tf=tempfile.NamedTemporaryFile(dir=self.UPLOAD_DIR, delete=False)
        self.receivedDataName=self.tf.name
        self.dgst=hashlib.sha256()
        def data(self, buffer):
            self.dgst.update(buffer)
            self.tf.write(buffer)
        def close(self):
            self.tf.close()
            self.receivedSha256=self.dgst.hexdigest()
            self.receivedOriginalFileName=self.fieldFileName.decode('utf-8')
            self.receivedSize=self.count
        self.fieldClose=close
        self.fieldData=data


    def setup_field_sig(self):
        self.tf=tempfile.NamedTemporaryFile(dir=self.UPLOAD_DIR, delete=False)
        self.receivedSigName=self.tf.name
        def data(self, buffer):
            if self.count<=1024*16 :
                self.tf.write(buffer)
            else:
                print("too much data for %s, ignore"%self.fieldName)

        def close(self):
            self.tf.close()
        self.fieldClose=close
        self.fieldData=data

    def setup_field_from(self):
        self.receivedFrom=b''
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
        if self.fieldName==None: return
        print("finish field %s"%self.fieldName)
        if self.fieldClose!=None:
            self.fieldClose(self)
        else:
            print("W7M1838T3E7DKHzdQ no field closer")
        self.fieldClose=None
        self.fieldData=None

    def discardFiles(self):
            if self.receivedSigName!=None: os.remove(self.receivedSigName)
            if self.receivedDataName!=None: os.remove(self.receivedDataName)
            self.receivedSigName=None
            self.receivedDataName=None

    def finalizeForm(self):
        with open(os.path.join(self.UPLOAD_DIR,self.LOG),"a") as log:
            now=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if (
                self.receivedFrom==None
                or self.receivedSigName==None
                or self.receivedDataName==None
            ):
                self.discardFiles()
                if self.receivedFrom==None: self.receivedFrom="<discard>"
                log.write("%s,%s,<none>,%s,%d,%s\n"%(now,
                self.receivedFrom,
                self.receivedSha256,
                self.receivedSize,
                self.receivedOriginalFileName))
                self.receivedFrom=None
            else:
                # verify signature
                rc=os.system("%s %s %s"%
                    (os.path.join(SCRIPT_DIR,"validate.sh"),
                    self.receivedDataName,
                    self.receivedSigName))
                if rc!=0:
                    self.discardFiles()
                    log.write("%s,%s,%s,%s,%d,%s\n"%(now,
                    self.receivedFrom,
                    "<badsignature>",
                    self.receivedSha256,
                    self.receivedSize,
                    self.receivedOriginalFileName))
                    return
                # if successful, rename signature file and log
                os.rename(self.receivedSigName,self.receivedDataName+".shig")
                self.receivedDataName=os.path.basename(self.receivedDataName)
                log.write("%s,%s,%s,%s,%d,%s\n"%(now,
                self.receivedFrom,
                self.receivedDataName,
                self.receivedSha256,
                self.receivedSize,
                self.receivedOriginalFileName))

