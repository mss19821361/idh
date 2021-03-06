import sys
from math import *
from java.lang import *
from java.util import *
from java.nio import *
from javax.swing import *

from edu.mines.jtk.awt import *
from edu.mines.jtk.dsp import *
from edu.mines.jtk.io import *
from edu.mines.jtk.mosaic import *
from edu.mines.jtk.util import *
from edu.mines.jtk.util.ArrayMath import *

from lcc import *

True = 1
False = 0

#############################################################################
# parameters

fontSize = 24
width = 500
height = 520
widthColorBar = 80
dataDir = "/data"
#pngDir = "./png"
pngDir = None

n1 = 315
n2 = 315
small = 0.01
lof = LocalOrientFilter(8)

#############################################################################
# functions

def main(args):
  #doImage();
  #doSymTest()
  #doSymDipTest()
  #goLinear()
  #goPlane()
  #goNotch()
  #goAmp()
  goDip()
  #goIdeal()
  #goDiff()
  #goAmpDiff()
  return

def goIdeal():
  for dip in [20,40,60,80]:
    suffix = str(dip)
    ai = makeIdeal(dip)
    plotf(ai,"ai"+suffix)

def goLinear():
  x = readImage()
  plot(x,10.0)
  u1 = zerofloat(n1,n2)
  u2 = zerofloat(n1,n2)
  el = zerofloat(n1,n2)
  lof.applyForNormalLinear(x,u1,u2,el)
  plot(el)
  xl = mul(x,el)
  xi = sub(x,xl)
  plot(xl,10.0)
  plot(xi,10.0)

def goDip():
  sd = 0.00
  sn = 0.002
  #doDip(LocalDipFilter.Factor.NOT,sd,sn)
  #doDip(LocalDipFilter.Factor.PCG,sd,sn)
  doDip(LocalDipFilter.Factor.INV,sd,sn)
  #doDip(LocalDipFilter.Factor.ALL,sd,sn)

def doDip(factor,sd,sn):
  ldf = LocalDipFilter(factor)
  for dip in [-88,-60,-40,-20,0,20,40,60,88]:
    x,u1,u2 = makeImpulse(dip)
    v1 = neg(u2)
    vw = fillfloat(sn,len(x[0]),len(x))
    if sn>0.0:
      suffix = "hn"+str(dip)
    elif sd>0.0:
      suffix = "hd"+str(dip)
    else:
      suffix = "hb"+str(dip)
    #y = applyLdfForward(ldf,sd,sn,v1,x)
    #y = applyLdfInverse(ldf,sd,sn,v1,x)
    #return
    y =  copy(x)
    ldf.applyLineFilter(vw,v1,x,y)
    a = frequencyResponse(y)
    plotf(a,"a"+suffix)
  x = readImage()
  #x = transpose(x)
  #x = makeTargetImage()
  v1 = getV1(x)
  n1,n2 = len(x[0]),len(x)
  #vw = mul(0.1,randfloat(n1,n2))
  vw = zerofloat(n1,n2)
  for i2 in range(n2):
    for i1 in range(n1):
      if n1/4<i1<3*n1/4 and n2/4<i2<3*n2/4:
        vw[i2][i1] = 0.01
      else:
        vw[i2][i1] = 1.00
  #y = applyLdfForward(ldf,sd,sn,u2,x)
  y =  copy(x)
  ldf.applyLineFilter(vw,v1,x,y)
  z = sub(x,y)
  plot(y,2.0,"yhd"+suffix)
  plot(z,10.0,"zhd"+suffix)
  #r = makeRandom()
  #r = smooth(r)
  #s = zerofloat(n1,n2)
  #ldf.applyInverse(sd,sn,u2,r,s)
  #plot(s,0.0,"s"+suffix)

def goNotch():
  #lpf1 = LocalPlaneFilter(LocalPlaneFilter.Type.HALE3,0.00)
  #lpf2 = LocalPlaneFilter(LocalPlaneFilter.Type.HALE3,0.01)
  lpf1 = LocalPlaneFilter(LocalPlaneFilter.Type.HALE7,0.00)
  lpf2 = LocalPlaneFilter(LocalPlaneFilter.Type.HALE7,0.05)
  for dip in [20,40,60,80]:
    suffix = str(dip)
    x,u1,u2 = makeImpulse(dip)
    y = applyLpfForward(lpf1,u1,u2,x)
    z = applyLpfInverse(lpf2,u1,u2,y)
    #w = inverseLaplacian(y)
    ay = frequencyResponse(y)
    az = frequencyResponse(z)
    #aw = frequencyResponse(w)
    plotf(ay,"ayhn"+suffix)
    plotf(az,"azhn"+suffix)
    #plotf(aw,"awhn"+suffix)
  x = readImage()
  x = transpose(x)
  plot(x,10.0,"xhn")
  u1,u2 = getU(x)
  y = applyLpfForward(lpf1,u1,u2,x)
  z = applyLpfInverse(lpf2,u1,u2,y)
  plot(y,2.0,"yhn")
  plot(z,2.0,"zhn")
  plot(sub(x,z),10.0,None)

def inverseLaplacian(x):
  n1 = len(x[0])
  n2 = len(x)
  df = DifferenceFilter()
  t = zerofloat(n1,n2)
  y = zerofloat(n1,n2)
  df.applyInverse(x,t)
  df.applyInverseTranspose(t,y)
  return y

def makeImpulse(angle):
  n1 = 105
  n2 = 105
  a = angle*pi/180.0
  c = cos(a)
  s = sin(a)
  x = zerofloat(n1,n2)
  x[(n2-1)/2][(n1-1)/2] = 1.0
  u1 = fillfloat(c,n1,n2)
  u2 = fillfloat(-s,n1,n2)
  return x,u1,u2

def makeIdeal(angle):
  n1 = 105
  n2 = 105
  j1 = (n1-1)/2
  j2 = (n2-1)/2
  s1 = 1.0/(n1-1)
  s2 = 1.0/(n2-1)
  a = angle*pi/180.0
  v1 = sin(a)
  v2 = cos(a)
  ai = zerofloat(n1,n2)
  for i2 in range(n2):
    k2 = (i2-j2)*s2
    for i1 in range(n1):
      k1 = (i1-j1)*s1
      if k1==0.0 and k2==0.0:
        ai[i2][i1] = 0.0
      else:
        s = v1*k1+v2*k2
        t = 0.001+k1*k1+k2*k2
        ai[i2][i1] = 1.0-0.05/(0.05+s*s/t)
  return ai

def doImage():
  x = readImage()
  #x = transpose(x)
  #x = makePlaneImage(63.435)
  #x = makePlaneImage(30)
  #x = makeTargetImage()
  #x = flip2(x)
  plot(x,10.0,"x")
  return x

def goAmp():
  for dip in [20,40,60,80]:
    suffix = str(dip)
    #doAmp(dip,LocalPlaneFilter.Type.FOMEL1,"af1"+suffix)
    #doAmp(dip,LocalPlaneFilter.Type.CLAERBOUT1,"ac1"+suffix)
    doAmp(dip,LocalPlaneFilter.Type.HALE2,"ah2"+suffix)
    #doAmp(dip,LocalPlaneFilter.Type.HALE3,"ah3"+suffix)
    #doAmp(dip,LocalPlaneFilter.Type.HALE5,"ah5"+suffix)
    doAmp(dip,LocalPlaneFilter.Type.HALE7,"ah7"+suffix)

def goAmpDiff():
  for dip in [20,40,60,80]:
    suffix = str(dip)
    doAmpDiff(dip,"ahs"+suffix)

def goPlane():
  x1 = readImage()
  x2 = transpose(x1)
  x3 = makeTargetImage()
  for x,s in [(x1,"_1"),(x2,"_2"),(x3,"_3")]:
  #for x,s in [(x2,"_2")]:
    plot(x,10.0,"x"+s)
    #doPlane(x,LocalPlaneFilter.Type.FOMEL1,"f1"+s)
    #doPlane(x,LocalPlaneFilter.Type.CLAERBOUT1,"c1"+s)
    #doPlane(x,LocalPlaneFilter.Type.HALE2,"h2"+s)
    #doPlane(x,LocalPlaneFilter.Type.HALE3,"h3"+s)
    #doPlane(x,LocalPlaneFilter.Type.HALE5,"h5"+s)
    #doPlane(x,LocalPlaneFilter.Type.HALE6,"h6"+s)
    doPlane(x,LocalPlaneFilter.Type.HALE7,"h7"+s)

def goDiff():
  x1 = readImage()
  x2 = transpose(x1)
  x3 = makeTargetImage()
  for x,s in [(x1,"_1"),(x2,"_2"),(x3,"_3")]:
    plot(x,10.0,"x"+s)
    doDiff(x,"h3"+s)

def makeRandom():
  r = Random(314159)
  return sub(randfloat(r,n1,n2),0.5)

def doPlane(x,type,png):
  u1,u2 = getU(x)
  lpf = LocalPlaneFilter(type,small)
  y = zerofloat(n1,n2)
  z = zerofloat(n1,n2)
  r = makeRandom()
  r = smooth(r)
  s = zerofloat(n1,n2)
  lpf.applyForward(u1,u2,x,y)
  lpf.applyInverse(u1,u2,y,z)
  lpf.applyInverse(u1,u2,r,s)
  print "max |z-x| =",max(abs(sub(z,x)))
  plot(y,5.0,"y"+png)
  plot(z,10.0,"z"+png)
  plot(s,0.0,"s"+png)
  plot(sub(z,x),0.0,None)

def doDiff(x,png):
  u1,u2 = getU(x)
  su = fillfloat(0.0,n1,n2)
  sv = fillfloat(1.0,n1,n2)
  sigma = sqrt(2.0/3.0)*sqrt(2.0/small)
  ldf = LocalDiffusionFilter(sigma)
  y = zerofloat(n1,n2)
  z = zerofloat(n1,n2)
  r = makeRandom()
  r = smooth(r)
  s = zerofloat(n1,n2)
  ldf.apply(su,sv,u2,x,y)
  y = sub(x,y)
  ldf.apply(su,sv,u2,r,s)
  plot(y,5.0,"ys"+png)
  plot(s,0.0,"ss"+png)

def doAmpDiff(dip,png=None):
  x,u1,u2 = makeImpulse(dip)
  h = copy(x)
  su = copy(x)
  sv = copy(x)
  fill(0.0,su)
  fill(1.0,sv)
  sigma = sqrt(2.0/3.0)*sqrt(2.0/small)
  ldf = LocalDiffusionFilter(sigma)
  ldf.apply(su,sv,u2,x,h)
  h = sub(x,h)
  ah = frequencyResponse(h)
  plotf(ah,png)

def doAmp(dip,type,png=None):
  lpf = LocalPlaneFilter(type)
  x,u1,u2 = makeImpulse(dip)
  h = applyLpfForward(lpf,u1,u2,x)
  ah = frequencyResponse(h)
  plotf(ah,png)

def doSymTest():
  x = makeTargetImage()
  lpf = LocalPlaneFilter(LocalPlaneFilter.Type.HALE5)
  u1 = randfloat(n1,n2)
  u2 = randfloat(n1,n2)
  x = sub(randfloat(n1,n2),0.5)
  y = sub(randfloat(n1,n2),0.5)
  ax = zerofloat(n1,n2)
  ay = zerofloat(n1,n2)
  lpf.applyForward(u1,u2,x,ax)
  lpf.applyForward(u1,u2,y,ay)
  yax = sum(mul(y,ax))
  xay = sum(mul(x,ay))
  print "yax =",yax," xay=",xay

def doSymDipTest():
  x = makeTargetImage()
  ldf = LocalDipFilter(LocalDipFilter.Factor.ALL)
  u2 = randfloat(n1,n2)
  x = sub(randfloat(n1,n2),0.5)
  y = sub(randfloat(n1,n2),0.5)
  ax = zerofloat(n1,n2)
  ay = zerofloat(n1,n2)
  ldf.applyForward(0.01,0.01,u2,x,ax)
  ldf.applyForward(0.01,0.01,u2,y,ay)
  yax = sum(mul(y,ax))
  xay = sum(mul(x,ay))
  print "yax =",yax," xay=",xay

def applyLdfForward(ldf,sd,sn,u2,x):
  y = copy(x)
  if sd>0 and sn==0.0:
    ldf.applyDip(sd,u2,x,y)
  elif sd==0.0 and sn>0:
    ldf.applyNotch(sn,u2,x,y)
  else:
    ldf.applyForward(sd,sn,u2,x,y)
  return y

def applyLdfInverse(ldf,sd,sn,u2,x):
  y = copy(x)
  ldf.applyInverse(sd,sn,u2,x,y)
  return y

def applyLpfInverse(lpf,u1,u2,x):
  y = copy(x)
  lpf.applyInverse(u1,u2,x,y)
  return y

def applyLpfForward(lpf,u1,u2,x):
  y = copy(x)
  lpf.applyForward(u1,u2,x,y)
  return y

def applyLpfInverse(lpf,u1,u2,x):
  y = copy(x)
  lpf.applyInverse(u1,u2,x,y)
  return y

def frequencyResponse(x):
  n1 = len(x[0])
  n2 = len(x)
  n1 = FftComplex.nfftSmall(n1)
  n2 = FftComplex.nfftSmall(n2)
  xr = copy(n1,n2,x)
  xi = zerofloat(n1,n2)
  cx = cmplx(xr,xi)
  fft1 = FftComplex(n1)
  fft2 = FftComplex(n2)
  fft1.complexToComplex1(1,n2,cx,cx)
  fft2.complexToComplex2(1,n1,cx,cx)
  ax = cabs(cx)
  a = zerofloat(n1,n2)
  j1 = n1/2
  j2 = n2/2
  copy(n1-j1,n2-j2,0,0,ax,j1,j2,a)
  copy(j1,j2,n1-j1,n2-j2,ax,0,0,a)
  copy(n1-j1,j2,0,n2-j2,ax,j1,0,a)
  copy(j1,n2-j2,n1-j1,0,ax,0,j2,a)
  return a

def smooth(x):
  n1 = len(x[0])
  n2 = len(x)
  t = zerofloat(n1,n2)
  y = zerofloat(n1,n2)
  rgf = RecursiveGaussianFilter(1.0)
  rgf.apply0X(x,t)
  rgf.applyX0(t,y)
  """
  bf = ButterworthFilter(0.25,2,ButterworthFilter.Type.LOW_PASS)
  bf.apply1Forward(x,t)
  bf.apply1Reverse(t,y)
  bf.apply2Forward(y,t)
  bf.apply2Reverse(t,y)
  """
  return y

def readImage():
  fileName = dataDir+"/seis/vg/junks.dat"
  ais = ArrayInputStream(fileName,ByteOrder.LITTLE_ENDIAN)
  f = zerofloat(n1,n2)
  ais.readFloats(f)
  ais.close()
  return f

def makeTargetImage():
  k = 0.3
  c1 = n1/2
  c2 = n2/2
  f = zerofloat(n1,n2)
  for i2 in range(n2):
    d2 = i2-c2
    for i1 in range(n1):
      d1 = i1-c1
      f[i2][i1] = 10.0*sin(k*sqrt(d1*d1+d2*d2))
  return f

def makePlaneImage(angle):
  a = angle*pi/180.0
  k = 0.3
  c = k*cos(a)
  s = k*sin(a)
  return mul(10.0,sin(rampfloat(0.0,c,s,n1,n2)))

def flip2(f):
  n1 = len(f[0])
  n2 = len(f)
  g = zerofloat(n1,n2)
  for i2 in range(n2):
    copy(f[n2-1-i2],g[i2])
  return g

def getU(x):
  n1 = len(x[0])
  n2 = len(x)
  u1 = zerofloat(n1,n2)
  u2 = zerofloat(n1,n2)
  lof.applyForNormal(x,u1,u2)

def getV1(x):
  n1 = len(x[0])
  n2 = len(x)
  v1 = zerofloat(n1,n2)
  lof.apply(x,None,None,None,v1,None,None,None,None)
  return v1

#############################################################################
# plot

def plot(f,clip=0.0,png=None):
  n1 = len(f[0])
  n2 = len(f)
  p = panel()
  s1 = Sampling(n1,1.0,0.0)
  s2 = Sampling(n2,1.0,0.0)
  if n1<50 and n2<50:
    s1 = Sampling(n1,1,-(n1-1)/2)
    s2 = Sampling(n2,1,-(n2-1)/2)
  pv = p.addPixels(s1,s2,f)
  if clip!=0.0:
    pv.setClips(-clip,clip)
  else:
    pv.setPercentiles(0.0,100.0)
  pv.setInterpolation(PixelsView.Interpolation.NEAREST)
  frame(p,png)

def plotf(f,png=None):
  n1 = len(f[0])
  n2 = len(f)
  p = panel()
  pv = p.addPixels(f)
  pv.setColorModel(ColorMap.JET)
  pv.setInterpolation(PixelsView.Interpolation.LINEAR)
  frame(p,png)

def panel():
  p = PlotPanel(1,1,
    PlotPanel.Orientation.X1DOWN_X2RIGHT,
    PlotPanel.AxesPlacement.NONE)
  #p.addColorBar()
  #p.setColorBarWidthMinimum(widthColorBar)
  return p

def frame(panel,png=None):
  frame = PlotFrame(panel)
  frame.setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE)
  frame.setFontSize(fontSize)
  frame.setSize(width,height)
  frame.setVisible(True)
  if png and pngDir:
    frame.paintToPng(100,6,pngDir+"/"+png+".png")
  return frame

#############################################################################
# Do everything on Swing thread.

class RunMain(Runnable):
  def run(self):
    main(sys.argv)
SwingUtilities.invokeLater(RunMain())
