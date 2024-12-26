# (c) 2024 SA6HBR
#

from imports.si4703Library import rdsRadio
import time

resetPin_id = 13
sdioPin_id = 4
sclkPin_id = 5
radio = rdsRadio(0x10, resetPin_id, sdioPin_id, sclkPin_id)

def menu():
    print ()
    print ('pu - Power up','pd - Power down','2  - Seek up','1  - Seek down','+  - Volume up','-  - Volume down','4A - Get time from RDS','More RDS: 0A, 1A, 2A, 10A and 14A', sep='\n')
    

try:
    while True:
        print ()
        PS = radio.getPowerStatus()
        if (PS==0):
            menu()
            print ()
            print ("Status - Power Down")
            print ("Write pu + ENTER for start si4703-chip")
        else:
            print (("  "+str(radio.getChannel()/10))[-5:] + " MHz - RSSI: " + str(radio.getRSSI()) + " Vol: " + str(radio.getVolume()) + " " + radio.getProgramService())
            
        kbdInput = input(">>").upper()          
        
        if (PS==1):
            if kbdInput == "2":radio.radioSeekUp()
            if kbdInput == "1":radio.radioSeekDown()
            if kbdInput == "+":radio.setVolume(radio.getVolume()+1)
            if kbdInput == "-":radio.setVolume(radio.getVolume()-1)

            if kbdInput == "3":radio.getAllChannel()                 # Get a list of all radio-channels
            if kbdInput == "4":radio.getRDS()                        # Get a random rds-message
            if kbdInput == "5":radio.getRDS(1,0,"XX")                # Get TP, PTY, PI
            if kbdInput == "6":radio.getSomeMessagesRDS(50,10000, 0) # read some rds-message
            if kbdInput == "7":radio.getSomeMessagesRDS(50,60000, 1) # read only unknown
            if kbdInput == "8":print(', '.join([str(hex(i)) for i in radio.viewRadioRegisters()])) #view RadioRegisters
            
            if kbdInput in ("0A","1A","2A","10A","14A")     :radio.getSomeMessagesRDS(50, 5000, 0,kbdInput)
            elif (kbdInput not in ("pu","pd") and len(kbdInput)>=2) :radio.getSomeMessagesRDS(50, 60000, 0,kbdInput)
            
        if kbdInput == "PU":radio.powerUp()
        if kbdInput == "PD":radio.powerDown()
        if kbdInput == "Q":break
        if kbdInput == "":menu()
        
except KeyboardInterrupt:
        print ("Exit")
        
radio.PowerDown()
print ("Exit program")
