# Copyright 2019, Teus Hagen, GPLV4
# simple test to see if meteo I2C device is present
from time import sleep_ms
from machine import I2C

__version__ = "0." + "$Revision: 3.8 $"[11:-2]
__license__ = 'GPLV4'

# connect I2C to Gnd
def PwrI2C(pins, i2c=None):
    if type(pins[2]) is str:
      from machine import Pin
      if not Pin(pins[2], mode=Pin.OUT, pull=None, alt=-1).value():
        print("Activate I2C bus")
        Pin(pins[2], mode=Pin.OUT, pull=None, alt=-1).value(1)
        sleep_ms(200)
        if i2c:
          i2c.init(I2C.MASTER, pins=pins[:2])
          sleep_ms(200)
      return True
    return False

def chip_ID(pins, i2c, address=0x77): # I2C dev optional ID
    chip_ID_ADDR = const(0xd0)
    # Create I2C device.
    if not type(i2c) is I2C:
      raise ValueError('An I2C object is required.')
    ID = 0 # 12 bits name, 9 bits part nr, 3 bits rev
    if type(pins[2]) is str: PwrI2C(pins)
    try: ID = i2c.readfrom_mem(address, chip_ID_ADDR, 3)
    except Exception as e: 
        print("Unable to read I2C chip ID: %s" % e)
    # print("ID: ", ID)
    return int.from_bytes( ID,'little') & 0xFF

BME280_ID = const(0x60)
BME680_ID = const(0x61)
SSD1306_ID = const(0x3)

# side effect: I2C pwr/gnd enabled
def searchDev(names=['BME','SHT','SSD']):
    I2Cpins = [('P23','P22',None)] # I2C pins [(SDA,SCL,Pwr), ...]
    I2Cdevices = [
            ('BME280',0x76),('BME280',0x77), # BME serie Bosch
            ('SHT31',0x44),('SHT31',0x45),   # Sensirion serie
            ('SSD1306',0x3c)                 # oled display
       ]
    # print("Wrong wiring may hang I2C address scan search...")
    try: from Config import I2Cpins
    except: pass
    print("Using I2C SDA/SCL/Pwr pins: ", I2Cpins)
    try: from Config import I2Cdevices
    except: pass
    print("Search for I2C devices", I2Cdevices)
    bus = None; device = None; address = None; nr = None
    for index in range(0,len(I2Cpins)):
        if len(I2Cpins[index]) == 2:
          I2Cpins[index] = tuple(list(I2Cpins[index])+[None])
        cur_i2c = I2C(index, I2C.MASTER, pins=I2Cpins[index][:2]) # master
        if PwrI2C(I2Cpins[index], cur_i2c):
            print("I2C bus %d is activated" % index)
        regs = cur_i2c.scan(); sleep_ms(100)
        for item in I2Cdevices:
            if type(item) is tuple: item = list(item)
            if item[1] in regs:
                ID = chip_ID(I2Cpins[index],cur_i2c, item[1])
                if item[0][:3] == 'BME':
                  if ID == BME680_ID: item[0] = 'BME680'
                  elif ID != BME280_ID: raise IOError("Unknown BME id 0x%X" % ID)
                print('%s ID=0x%X I2C[%d]:' % (item[0],ID,index), ' SDA~>%s, SCL~>%s, pwr~>' % I2Cpins[index][:2], I2Cpins[index][2],', reg 0x%2X' % item[1])
                if not item[0][:3] in names: continue
                if device: continue  # first one we use
                device = item[0]; bus = cur_i2c; nr = index
                address = item[1]
    return(nr,bus,device,address)

useSSD = 'I2C'
try: from Config import useSSD
except: pass
oled = None
if useSSD:
  try:
    try: import SSD1306
    except: raise ImportError("library SSD1306 missing")
    width = 128; height = 64  # display sizes
    if useSSD == 'I2C': # display may flicker on reload
      (nr,i2c,oled,addr) = searchDev(names=['SSD'])
      if not addr: raise ValueError("No I2C oled display found.")
      print("Found I2C[%d] device %s" % (nr,oled))
      oled = SSD1306.SSD1306_I2C(width,height,i2c,addr=addr)
    elif useSSD == 'SPI': # for fast display
      try:
        from Config import S_CLKI, S_MOSI, S_MISO  # SPI pins config
      except:
        S_DC = 'P10'; S_MOSI = 'P11'; S_MISO = 'P14'  # SSD defaults
      try:
        from Config import S_DC, S_RES, S_CS      # GPIO SSD pins
      except:
        S_DC = 'P5'; S_RES = 'P6'; S_CS = 'P7'    # SSD default pins
      from machine import SPI
      print('Oled SPI: DC ~> %s, CS ~> %s, RST ~> %s, D1/MOSI ~> %s, D0/CLK ~> %s' % (S_DC,S_CS,S_RES,S_MOSI,S_CLKI))
      spi = SPI(0,SPI.MASTER, baudrate=100000,pins=(S_CLKI, S_MOSI, S_MISO))
      oled = SSD1306.SSD1306_SPI(width,height,spi,S_DC, S_RES, S_CS)
    else:
      oled = None
      print("Incorrect display bus %s" % useSSD)
    if oled:
      oled.fill(1) ; oled.show(); sleep_ms(1000)
      oled.fill(0); oled.show()
  except Exception as e:
    oled = None
    print('Oled display failed: %s' % e)
    import sys
    sys.exit()

# found oled, try it and blow RGB led wissle
from machine import unique_id
from machine import Pin
import binascii
try:
  from led import LED
except:
  raise OSError("Install library led")

import pycom

def sleep(secs):
    sleep_ms(int(secs*1000.0))

#button = Pin('P10',mode=Pin.IN, pull=Pin.PULL_UP)
#led = Pin('P9',mode=Pin.OUT)
#
#def pressed(what):
#  # global LED
#  print("Pressed %s" % what)
#  # LED.blink(5,0.1,0xff0000,False)
#
#  global led
#  led.toggle()
#
#button.callback(Pin.IRQ_FALLING|Pin.IRQ_HIGH_LEVEL,handler=pressed,arg='STOP')

def display(txt,x,y,clear, prt=True):
  ''' Display Text on OLED '''
  global oled
  if oled:
    if clear:
      oled.fill(0)
    oled.text(txt,x,y)
    oled.show()
  if prt:
    print(txt)

def rectangle(x,y,w,h,col=1):
  global oled
  if not oled: return
  ex = int(x+w); ey = int(y+h)
  for xi in range(int(x),ex):
    for yi in range(int(y),ey):
      oled.pixel(xi,yi,col)

def ProgressBar(x,y,width,height,secs,blink=0,slp=1):
  global oled, LED
  rectangle(x,y,width,height)
  if (height > 4) and (width > 4):
    rectangle(x+1,y+1,width-2,height-2,0)
    x += 2; width -= 4;
    y += 2; height -= 4
  elif width > 4:
    rectangle(x+1,y,width-2,height,0)
    x += 2; width -= 4;
  else:
    rectangle(x,y,width,height,0)
  step = width/(secs/slp); xe = x+width; myslp = slp
  if blink: myslp -= (0.1+0.1)
  for sec in range(int(secs/slp+0.5)):
    if blink:
      LED.blink(1,0.1,blink,False)
    sleep(myslp)
    if x > xe: continue
    rectangle(x,y,step,height)
    if oled: oled.show()
    x += step
  return True

try:
    # Turn off hearbeat LED
    pycom.heartbeat(False)
    display('test bar',0,0,True)
    if not ProgressBar(0,34,128,8,12,0xebcf5b,1):
        LED.blink(5,0.3,0xff0000,True)
    else: LED.blink(5,0.3,0x00ff00,False)
    display("MySense PyCom",0,0,True)
    myID = binascii.hexlify(unique_id()).decode('utf-8')
    display("s/n " + myID, 0, 16, False)
except Exception as e:
    print("Failure: %s" % e)
print("DONE. Soft reset.")
import sys
sys.exit()
