from FormDataParser import FormDataParser
from dataclasses import dataclass
import tempfile
import hashlib
import os
import datetime

class MultiUploadParser(FormDataParser):
    @dataclass
    class DataInfo:
        tempName:str
        originalName:str='?'
        sha256:str='<unknown>'
        size:int=0

    def __init__(self,boundary, upload):
        super().__init__(boundary)
        self.UPLOAD_DIR=upload
        self.LOG="upload.log"
        self.count=0
        # to succeed, the form must contain these 3 fields
        self.receivedFrom=None
        self.receivedDataInfo=[]
        self.dgst=None # intermediate digest for currently receiving data
        self.fieldClose=None
        self.fieldData=None

    def setup_field_data(self):
        self.tf=tempfile.NamedTemporaryFile(dir=self.UPLOAD_DIR, delete=False)
        # there used to be local variable here which was supposed to be bound
        # in a closure, but when the function is called, it complained
        # receivedDataInfo.sha256=self.dgst.hexdigest()
        # NameError: name 'receivedDataInfo' is not defined
        self.currentData=self.DataInfo(tempName:=self.tf.name)
        self.dgst=hashlib.sha256()
        def data(self, buffer):
            self.dgst.update(buffer)
            self.tf.write(buffer)
        def close(self):
            self.tf.close()
            self.currentData.sha256=self.dgst.hexdigest()
            self.currentData.originalName=self.fieldFileName.decode('utf-8')
            self.currentData.size=self.count
            self.receivedDataInfo.append(self.currentData)
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
            print("W6256G69LVVFNJ5VX data processor is not defined")


    def finalizeHeaders(self):
        print("received field %s",self.fieldName)
        if self.fieldName==b'data' : self.setup_field_data()
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
            print("WKGBASJJ0RXIJJGIN no field closer")
        self.fieldClose=None
        self.fieldData=None

    def discardFiles(self):
        for fi in self.receivedDataInfo:
            os.remove(fi.tempName)
        self.receivedDataInfo=[]

    def finalizeForm(self):
        with open(os.path.join(self.UPLOAD_DIR,self.LOG),"a") as log:
            now=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            todelete=[]
            for i,fi in enumerate(self.receivedDataInfo):
                if fi.size==0:
                    todelete.append(i)
                    os.remove(fi.tempName)
                else:
                    log.write("%s,%s,%s,%s,%d,%s\n"%(now,
                    self.receivedFrom,
                    os.path.basename(fi.tempName),
                    fi.sha256,
                    fi.size,
                    fi.originalName))
            for i in reversed(todelete):
                del self.receivedDataInfo[i]


