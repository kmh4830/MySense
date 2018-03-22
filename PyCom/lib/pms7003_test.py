# standalone test loop
from time import time, sleep
from PMSx003 import PMSx003

sensor = PMSx003(port=1, debug=True, sample=60, interval=0)
errors = 0
while True:
    timings = time()
    try:
      # sensor.GoActive() # fan on wait 60 secs
      data = sensor.getData()
    except Exception as e:
      print("PMS read error raised as: %s" % e)
      if errors > 20: break
      errors += 1
      sleep(30)
      sensor.ser.readall()
      continue
    errors = 0
    print("PMS record:")
    print(data)
    timings = 5*60 -(time()-timings)
    if timings > 0:
        print("Sleep now for %d seconds" % timings)
        try:
            sensor.Standby()
            if timings > 60: sleep(timings-60)
            sensor.Normal() # fan on measuring
            sleep(60)
            sensor.mode = 0 # active
        except:
            errors += 1
            sleep(60)
