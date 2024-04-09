import time
import RPi.GPIO as GPIO

from gpiozero import Button

# GPIO17 #YELLOW (PIN11)
# GPIO27 #GREEN  (PIN13) 
# GPIO22 #BLUE   (PIN15)
# GPIO23 #VIOLET (PIN16)
GPIO17 = 17
GPIO27 = 27
GPIO22 = 22
GPIO23 = 23


YELLOW = GPIO17 
GREEN  = GPIO27 
BLUE   = GPIO22 
VIOLET = GPIO23 


print("Setting up GPIO")
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(YELLOW, GPIO.IN, GPIO.PUD_DOWN)

while True:
    time.sleep(1)
    if GPIO.input(YELLOW):
        print("button is pressed")
