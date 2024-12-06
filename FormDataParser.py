from enum import Enum
import os

class FormDataParser:
    MAXHEADERLENGTH=16384
    BPREFIX=b"--"
    CRLF=b"\r\n"
    BUFFERSIZE=64*1024
    
    class LookFor(Enum):
        HeaderLine=1
        CRLF=2
        Boundary=3
        EOF=4

    def __init__(self, boundary):
        self.boundary=self.CRLF+self.BPREFIX+bytes(boundary,'utf8')
        self.initializeField()
        self.headerLine=b''
        self.headerName=None
        self.headerValue=None

    # override this to do your own field processing
    def processPartialFieldData(self,buffer):
        print(">FLDT> %s:%s"%(self.fieldName,buffer))

    def processPartialHeaderLine(self,buffer):
        # HTTP limits the size of header lines
        if len(self.headerLine)+len(buffer)>self.MAXHEADERLENGTH:
            print("W9UX6RT8FBL5J0BAT header is too long")
        else:
            self.headerLine+=buffer
            # print(">HLSF> %s"%self.headerLine)

    def finalizeHeaderLine(self):
        # print(".. finalizeHeaderLine")
        i=None
        try:
            i=self.headerLine.index(b":")
        except:
            self.headerValue=self.headerLine
            self.headerName=None
            if len(self.headerLine)>0:
                print("WNCZZZLIE1HMZAW3C no header name in %s"%self.headerLine)
            else:
                # entirely empty header line is acceptable
                pass
            self.headerLine=b''
            return
        self.headerName=self.headerLine[0:i].lower().strip(b' ')
        self.headerValue=self.headerLine[(i+1):]
        self.headerLine=b''
        match self.headerName:
            case b'content-type':
                self.fieldType=self.headerValue.strip(b' ')
            case b'content-disposition':
                self.parseContentDisposition(self.headerValue)
            case _:
                print("WEMSRWSHXOHM11B3C unknown header %s"%headerName)
        # print(">head> n=%s f=%s t=%s"%(self.fieldName,self.fieldFileName,self.fieldType))

    def parseContentDisposition(self,value):
        parts=value.split(b';')
        # print(">prts> %s"%parts)
        if parts[0].lower().strip(b' ')!= b'form-data':
            print("WV9BP1KOX5X8V9OEK unexpected disp %s"%parts[0])
        self.fieldName=None
        self.fieldFileName=None
        for p in parts[1:]:
            try:
                n,v=p.split(b'=',1)
                n=n.lower().strip(b' ')
                v=v.strip(b' ').strip(b'"')
                # print(">part>%s = %s"%(n,v))
                match n:
                    case b'name':
                        self.fieldName=v
                    case b'filename':
                        self.fieldFileName=v
            except ValueError:
                print("WWWKJL2CDC4YC3KLF bad part %s"%p)

    # override this to do your own field processing
    # called before field receives any data, but after all the headers are read
    def finalizeHeaders(self):
        # called when the empty line separating headers from data
        pass

    def initializeField(self):
        # initialize for next round
        self.fieldName=None
        self.fieldFileName=None
        self.fieldType=None

    # override this to do your own field processing
    # called when field data is complete and there will be no more
    # data for this field
    def finalizeField(self):
        print("done with the field %s/%s/%s"%(self.fieldType,self.fieldName,self.fieldFileName))

    def parse(self,stream,contentLength):
        eof=False
        bt=None
        b_leftover=self.CRLF
        b_latest=None
        lookFor=self.LookFor.Boundary
        totalRead=0
        while not eof:
            # b_latest=stream.read(self.BUFFERSIZE)
            toread=self.BUFFERSIZE
            if toread+totalRead>contentLength: toread=contentLength-totalRead
            totalRead+=toread
            # b_latest=os.read(stream.fileno(), toread)
            b_latest=stream.read(toread)
            if len(b_latest)<toread:
                print("<READ< EOF") 
                eof=True
            # print("<READ< %s %s"%(b_latest,eof))
            bt=b_leftover+b_latest
            while True:
                # print("..look for %s"%lookFor)
                # print("..leftover=%s"%b_leftover)
                # print("..      bt=%s"%bt)
                # may be looking for boundary or for header
                if lookFor==self.LookFor.Boundary:
                    i=None
                    try:
                        i=bt.index(self.boundary)
                    except:
                        # not found in the existing data, need to read more
                        self.processPartialFieldData(b_leftover)
                        break
                    if i+len(self.boundary)+2>len(bt):
                        # found the boundary, but do not know what is beyond it
                        # need next block to proceed
                        self.processPartialFieldData(b_leftover)
                        break
                    self.processPartialFieldData(bt[0:i])
                    self.finalizeField()
                    tail=bt[(i+len(self.boundary)):(i+len(self.boundary)+2)]
                    bt=bt[(i+len(self.boundary)+2):]
                    b_latest=bt
                    b_leftover=b''
                    if tail==self.CRLF:
                        # next part of multipart
                        # it may be in the remaining piece of the block
                        self.initializeField()
                        lookFor=self.LookFor.HeaderLine
                        if len(bt)>=self.BUFFERSIZE:
                            raise Exception("UH0FUVS2ZV6JAM5YQ")
                    elif tail==self.BPREFIX:
                        # terminating
                        lookFor=self.LookFor.EOF
                        eof=True
                    else:
                        # something unexpected after boundary
                        print("EAQ24XNCLEJ2JD27Y unexpected after boundary:"+tail)
                        # treat it like eof
                        lookFor=self.LookFor.EOF
                        eof=True
                elif lookFor==self.LookFor.HeaderLine:
                    i_eol=None
                    try:
                        i_eol=bt.index(self.CRLF)
                    except:
                        self.processPartialHeaderLine(b_leftover)
                        break;
                    self.processPartialHeaderLine(bt[0:i_eol])
                    self.finalizeHeaderLine()
                    bt=bt[(i_eol+2):]
                    b_latest=bt
                    b_leftover=b''
                    if self.headerName is None:
                        if self.headerValue==b'':
                            # entirely empty line = no more headers
                            self.finalizeHeaders()
                            # what follows is contents of a field
                            lookFor=self.LookFor.Boundary;
                        else:
                            print("EG4SN5KA7Z7HFUPIM invalid header line %s"%self.headerName)
                    else:
                        pass
                elif lookFor==self.LookFor.EOF:
                    break
                else:
                    raise Exception("UHXYSA9IV83EABYNI unknown clause %s"%lookFor)
            b_leftover=b_latest
        if totalRead<contentLength:
            print("stopped reading after %d/%d bytes"%(totalRead,contentLength))

if __name__ == "__main__":
    def parserTest(filename,boundary):
        print("<FILE< %s"%filename)
        print("<BNDR< %s"%boundary)

        parser=FormDataParser(boundary)
        file=open(filename,"rb",0)
        parser.parse(file)
        file.close()

    parserTest("test3333atg8","----WebKitFormBoundaryAYUMBAhpaSbb8bbJ")
    parserTest("testm5fhciqi","----WebKitFormBoundaryNP6cLEEh2ZnPPviI")

