import random

def pfw(weights):
    s=sum(weights)
    return [w/s for w in weights]

def weighted(probs,rnd):
    i=0
    while rnd>=probs[i]:
        rnd-=probs[i]
        i+=1
    return i

class Filler:
    def __init__(self,seed=None):
        if seed==None: self.g=random.Random()
        else: self.g=random.Random(seed)

    ENG_WL_P=pfw([3.16, 16.975, 21.192, 15.678, 10.852, 8.524, 7.724, 5.623,
    4.032, 2.766, 1.582, 0.917, 0.483, 0.262, 0.099, 0.05, 0.027, 0.022, 0.011,
    0.006, 0.005, 0.002, 0.001, 0.001, 0.001, 0.001, 0.001 ])

    ALP=[chr(ord('a')+i) for i in range(26)]


    def word(self):
        return ''.join([self.ALP[int(self.g.random()*len(self.ALP))] for _ in range(weighted(self.ENG_WL_P,self.g.random())+1) ])
    
    def linkword(self):
        w=self.word()
        if self.g.random()<0.01 :
            d=["../","","/"][weighted([1,20,3],self.g.random())]
            if d=="/": d=self.word()+d
            w='<a href="%s%s.html">%s</a>'%(d,w,w)
        return w
    
    def sentenceLength(self):
        return int(self.g.gammavariate(9,1.1))
    
    def sentence(self,length=None):
        if length==None: length=self.sentenceLength()
        sentence=self.sample(self.linkword,length)
        sentence[0]=sentence[0].capitalize()
        return ' '.join(sentence)+'.'
    
    def paragraphLength(self):
        return int(4+self.g.gammavariate(9,3))
    
    def sample(self,sampleGenerator,length):
        return [sampleGenerator() for _ in range(length)]
    
    def paragraph(self):
      return "<p>"+"\n".join(self.sample(self.sentence,self.paragraphLength()))+"</p>"
    
    def chapterLength(self):
        return int(self.g.gammavariate(3,2)+2)

    HTML5="""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:1em auto;max-width:40em;padding:0 .62em;font:1.2em/1.62 serif;}
h1,h2,h3,h4{line-height:1.2;font-family:sans-serif}
H1 {text-align:center;color:navy}
@media print{body{max-width:none}}
</style>
"""
    def html(self):
        h=[self.HTML5]
        tit=(' '.join(self.sample(self.word,self.g.randint(1,3)))).capitalize()
        h.append("<title>%s</title></head><body><h1>%s</h1>"%(tit,tit))
        h.append(self.paragraph())
        
        # chapters
        for _ in range(self.g.randint(3,5)):
            tit=(' '.join(self.sample(self.word,self.g.randint(1,3)))).capitalize()
            h.append("<h2>%s</h2>"%tit)
            h.append("\n".join(self.sample(self.paragraph, self.chapterLength())))
        
        
        h.append("</body></html>")
        return ''.join(h)

if __name__=='__main__':
    import sys
    seed=None
    if len(sys.argv)>1: seed=sys.argv[1]
    c=Filler(seed)
    print(c.html())
