# SI4703 Python Library
# (c) 2016 Ryan Edwards <ryan.edwards@gmail.com> 
# Ported from my Arduino library which was modified from Aaron Weiss @ SparkFun's original library
#
# (c) 2024 SA6HBR
# ReWrite all and added more RDS and converted to Raspberry Pi Pico
#
# Release Notes:
# 1.0    27-Mar-2016        Initial release     Ryan Edwards
# 2.0    24-Dec-2024        Update RDS          SA6HBR 
#

import time
from machine import Pin, I2C, RTC #SA6HBR

class rdsRadio():

    #Default 
    LOW              = 0
    HIGH             = 1
    RDSA             = 0x0C
    RDSB             = 0x0D
    RDSC             = 0x0E
    RDSD             = 0x0F
    defaultChannel   = 1038 # SR P4 103.8 Mhz
    radioRegister    = [0] * 16
    
    # Register00h. Device ID
    PN       = 0 #Part Number.
    MFGID    = 0 #Manufacturer ID.

    # Register01h. Chip ID
    REV      = 0 #Chip Version.
    DEV      = 0 #Device.
    FIRMWARE = 0 #Firmware Version.

    # Register02h. Power Configuration
    DSMUTE   = 0 #Softmute Disable.
    DMUTE    = 0 #Mute Disable.
    MONO     = 0 #Mono Select
    RDSM     = 0 #RDS Mode.
    SKMODE   = 0 #Seek Mode.
    SEEKUP   = 0 #Seek Direction.
    SEEK     = 0 #Seek.
    DISABLE  = 0 #powerUp Disable.
    ENABLE   = 0 #powerUp Enable.

    # Register04h. System Configuration 1 
    RDSIEN  = 0 # RDS Interrupt Enable
    STCIEN  = 0 # Seek/Tune Complete Interrupt Enable
    RDS     = 0 # RDS Enable
    DE      = 0 # De-emphasis
    AGCD    = 0 # AGC Disable
    BLNDADJ = 0 # Stereo/Mono Blend Level Adjustment
    GPIO3   = 0 # General Purpose I/O 3
    GPIO2   = 0 # General Purpose I/O 2
    GPIO1   = 0 # General Purpose I/O 1

    # Register05h. System Configuration 2
    SEEKTH   = 0 #RSSI Seek Threshold.
    BAND     = 0 #Band Select.
    SPACE    = 0 #Channel Spacing
    VOLUME   = 0 #Volume

    # Register06h. System Configuration 3
    SMUTER  = 0 # Softmute Attack/Recover Rate
    SMUTEA  = 0 # Softmute Attenuation
    VOLEXT  = 0 # Extended Volume Range
    SKSNR   = 0 # Seek SNR Threshold
    SKCNT   = 0 # Seek FM Impulse Detection Threshold.

    # Register07h. Test 1
    XOSCEN  = 0 # Crystal Oscillator Enable
    AHIZEN  = 0 # Audio High-Z Enable
    
    # Register0Ah. Status RSSI
    RDSR     = 0 #RDS Ready
    STC      = 0 #Seek/Tune Complete
    SFBL     = 0 #Seek Fail/Band Limit
    AFCRL    = 0 #AFC Rail
    RDSS     = 0 #RDS Synchronized.
    BLERA    = 0 #RDS Block A Errors
    ST       = 0 #Stereo Indicator
    RSSI     = 0 #Received Signal Strength Indicator

    # Register0Bh. ReadChannel
    BLERB    = 0 #RDS Block B Errors
    BLERC    = 0 #RDS Block C Errors
    BLERD    = 0 #RDS Block D Errors
    FIRSTCHANNEL = 875
    LASTCHANNEL  = 1080
    CHANNEL      = defaultChannel  

    def clearRDSinfo(self):
        # RDS Basic information
        self.TP               = 0
        self.PTY              = 0
        self.PiCountry        = 0
        self.PiType           = 0
        self.PiReferens       = 0
        
        # RDS Type 0 groups: Basic tuning and switching information
        self.TA               = 0
        self.ProgrammeService = [chr(0)] * 8
        
        # RDS Type 2 groups: RadioText
        self.RadioTextFlag    = 0
        self.RadioTextA       = [chr(0)] * 64
        self.RadioTextB       = [chr(0)] * 64
        
        # RDS Type 7 groups: RadioPaging
        self.RadioPagingFlag  = 0
        self.RadioPagingA     = [chr(0)] * 64
        self.RadioPagingB     = [chr(0)] * 64
        
        # RDS Type 10 groups: Programme Type Name
        self.ProgrammeTypeNameFlag  = 0
        self.ProgrammeTypeNameTextA = [chr(0)] * 8
        self.ProgrammeTypeNameTextB = [chr(0)] * 8    
    
    def __init__(self, i2cAddr, resetPin_id, sdioPin_id, sclkPin_id):
        
        # Configure I2C and GPIO
        self.i2CAddr  = i2cAddr        
        self.resetPin = Pin(resetPin_id, Pin.OUT)
        self.sdioPin  = Pin(sdioPin_id, Pin.OUT)
        self.sclkPin  = Pin(sclkPin_id, Pin.OUT)
        # To get the Si4703 inito 2-wire mode, SEN needs to be high and SDIO needs to be low after a reset
        # The breakout board has SEN pulled high, but also has SDIO pulled high. Therefore, after a normal power up
        # The Si4703 will be in an unknown state. RST must be controlled
        self.sdioPin.value(self.LOW)
        time.sleep(0.1)
        self.resetPin.value(self.LOW)
        time.sleep(0.1)
        self.resetPin.value(self.HIGH)
        time.sleep(0.1)        
        self.i2c = I2C(0, scl=self.sclkPin, sda=self.sdioPin)    
        self.clearRDSinfo()
        
    def writeRadioRegisters(self):
        # A write command automatically begins with register 0x02 so no need to send a write-to address
        # First we send the 0x02 to 0x07 control registers
        # In general, we should not write to registers 0x08 and 0x09
        
        # only need a list that holds 0x02 - 0x07: 6 words or 12 bytes
        i2cWriteBytes = bytearray(12)
        
        #move the shadow copy into the write buffer
        for i in range(0,6):
            i2cWriteBytes[i*2], i2cWriteBytes[(i*2)+1] = divmod(self.radioRegister[i+2], 0x100)

        # the "address" of the SMBUS write command is not used on the si4703 - need to use the first byte
        self.i2c.writeto_mem(self.i2CAddr, i2cWriteBytes[0], i2cWriteBytes[1:11])

    def readRadioRegisters(self):
        #Read the entire register control set from 0x00 to 0x0F
        numRegstersToRead = 16
        i2cReadBytes = bytearray(32)
        
        #Si4703 begins reading from register upper register of 0x0A and reads to 0x0F, then loops to 0x00.
        # SMBus requires an "address" parameter even though the 4703 doesn't need one
        # Need to send the current value of the upper byte of register 0x02 as command byte
        cmdByte = self.radioRegister[0x02] >> 8

        i2cReadBytes = self.i2c.readfrom_mem(self.i2CAddr, cmdByte, 32)
        regIndex = 0x0A
        
        #Remember, register 0x0A comes in first so we have to shuffle the array around a bit
        for i in range(0,16):
            self.radioRegister[regIndex] = (i2cReadBytes[i*2] * 256) + i2cReadBytes[(i*2)+1]
            regIndex += 1
            if regIndex == 0x10:
                regIndex = 0
       
    def powerUp(self):
        # To get the Si4703 inito 2-wire mode, SEN needs to be high and SDIO needs to be low after a reset
        # The breakout board has SEN pulled high, but also has SDIO pulled high. Therefore, after a normal power up
        # The Si4703 will be in an unknown state. RST must be controlled
        self.sdioPin.value(self.LOW)
        time.sleep(0.1)
        self.resetPin.value(self.LOW)
        time.sleep(0.1)
        self.resetPin.value(self.HIGH)
        time.sleep(0.1)        
        self.i2c = I2C(0, scl=self.sclkPin, sda=self.sdioPin)

        #Write address 07h (required for crystal oscillator operation).
        #Set the XOSCEN bit to power up the crystal.
        #Write data 8100h
        #Wait 500ms for the oscillator to stabilize
        self.readRadioRegisters()
        self.radioRegister[0x07] = 0x8100
        self.writeRadioRegisters()
        time.sleep(0.5)

        #Write address 02h (required).
        #Set the DMUTE bit to disable mute. Optionally mute can be disabled later when audio is needed.
        #Set the ENABLE bit high to set the powerUp state.
        #Set the DISABLE bit low to set the powerUp state.
        #Write data 4001h.
        self.readRadioRegisters()
        self.radioRegister[0x02] = 0x4001
        
        #3.4.4. RDS (04h.12)—RDS Enable (Si4701/Si4703 only)
        #This bit enables/disables the RDS function of the device. When set high, RDS is enabled and when set low, RDS is disabled.
        self.radioRegister[0x04] |= (1<<12)
        
        #3.4.3. DE (04h.11)—FM De-Emphasis
        #The amount is specified as the time constant of a simple RC filter.
        #Two options are available: 75 µs (0), used in the USA; and 50 µs (1) used in Europe, Australia, and Japan.
        self.radioRegister[0x04] |= (1<<11)

        #3.4.2. SPACE (05h.5:4)—FM Channel Spacing
        #The SPACE field defines the frequency steps that the least significant bit of the CHAN field represents.
        #This setting in conjunction with the BAND setting determines what frequency a given number in the CHAN register represents.
        #Selecting the proper spacing for the country the system will be used in will result in the best overall performance.
        #01 100 kHz (Europe / Japan)
        self.radioRegister[0x05] |= (1<<4)

        #Seek Settings Recommendations
        #Most Stations
        self.radioRegister[0x05] |= (0x00<<8) #SEEKTH - Seek RSSI Threshold
        self.radioRegister[0x06] |= (0x04<<4) #SKSNR - Good audio SNR threshold P.37
        self.radioRegister[0x06] |= (0x08<<0) #SKCNT - Allows more FM impulses p.37
        
        #VOLUME (05h.3:0)—Volume
        self.radioRegister[0x05] &= ~(0b1111) #Clear volume bits
        self.radioRegister[0x05] |= 0x0001 #Set volume to lowest
        
        #Update
        self.writeRadioRegisters()        
        time.sleep(.110) # Max powerUp time 110ms P.13

        self.setChannel(self.CHANNEL)

    def powerDown(self):
        self.readRadioRegisters()
        #To power down the device:
        #1. Si4703-C19 Errata Option 3: Set RDS = 0.
        #2. Set the ENABLE bit high and the DISABLE bit high to place the device in powerDown mode.
        #   Note that all register states are maintained so long as VIO is supplied and the RST pin is high.
        #3. Remove VA and VD supplies as needed.

        #Set AHIZEN. All other bits in this register should be maintained at the value last read
        self.radioRegister[0x07] |= (1<<14)
        
        #Set GPIO1/2/3 to digital low to reduce current consumption. All other bits in this register should be maintained at the value last read.
        self.radioRegister[0x04] &= ~(0b111111)
        
        #Clear the DMUTE bit to enable mute.
        self.radioRegister[0x02] &= ~(0b1<<14)
        
        #Set the ENABLE bit high
        self.radioRegister[0x02] |= (1<<0)
        
        #Set the DISABLE bit high
        self.radioRegister[0x02] |= (1<<6)
        
        self.writeRadioRegisters() # Update

        time.sleep(.110) # Max powerUp time 110ms P.13

    def getPowerStatus(self):
        self.readRadioRegisters()
        self.getRegister02hPowerConfiguration()
        return self.ENABLE

    def radioSeekUp(self):
        self.radioSeek(self.HIGH)
        
    def radioSeekDown(self):
        self.radioSeek(self.LOW)
    
    def radioSeek(self,seekDirection):
        self.readRadioRegisters()
        
        #3.6.2. SKMODE (02h.10)—Seek Band Limit Behavior Mode
        #Set the SKMODE high to stop seek at the band limits and low to wrap at the band limits. P.20
        self.radioRegister[0x02] |= (1<<10)
        
        #3.6.1. SEEKUP (02h.9)—Seek Direction
        #Set the SEEKUP bit high to seek up and low to seek down. P.20
        self.radioRegister[0x02] &= ~(0b1<<9)
        self.radioRegister[0x02] |= (seekDirection<<9)
        
        #3.6.3. SEEK (02h.8)—Seek
        #Set the SEEK bit high to begin the seek operation.
        self.radioRegister[0x02] |= (1<<8)
        
        self.writeRadioRegisters() #Seeking will now start
        
        #Poll to see if STC is set
        startTime = time.ticks_ms()
        while True:
            if(time.ticks_ms() - startTime > 60000) :break
            self.readRadioRegisters()

            #Read address 0Ah (required).
            self.getRegister0AhStatusRSSI()

            #The STC bit being set indicates tuning has completed.
            #The SF/BL bit being set indicates the seek operation searched the band without finding a channel meeting the seek criteria (SEEKTH, SKSNR, SKCNT).
            #if((self.STC == self.HIGH) or (self.SFBL == self.HIGH)): break
            if((self.STC == self.HIGH)): break
            time.sleep(0.1)
            
        self.readRadioRegisters()
        #3.6.3. SEEK (02h.8)—Seek
        # Set the SEEK bit low to end the tuning operation and to set the STC bit low.
        self.radioRegister[0x02] &= ~(0b1<<8)
        self.writeRadioRegisters()
        self.clearRDSinfo()

    def setChannel(self,channel):
        newChannel = channel
        newChannel -= self.FIRSTCHANNEL # e.g. 9730 - 8750 = 980
        
        self.readRadioRegisters()
        #Write address 03h (required).
        #Set the TUNE bit high to begin a tuning operation.
        self.radioRegister[0x03] |= (1<<15)
        #Set CHAN[9:0] bits to select the desired channel
        self.radioRegister[0x03] &= ~(0b1111111111)
        self.radioRegister[0x03] |= newChannel
        self.writeRadioRegisters()

        loop = 0
        while True:
            self.readRadioRegisters()

            #Read address 0Ah (required).
            self.getRegister0AhStatusRSSI()

            #The STC bit being set indicates tuning has completed.
            #The SF/BL bit being set indicates the seek operation searched the band without finding a channel meeting the seek criteria (SEEKTH, SKSNR, SKCNT).
            if((self.STC == self.HIGH) or (self.SFBL == self.HIGH)): break
            loop += 1
            if(loop > 10) : break
            time.sleep(1)

        self.readRadioRegisters()
        #Write address 03h (required).
        #Set the TUNE bit low to stop a tuning operation.
        self.radioRegister[0x03] &= ~(1<<15)
        self.writeRadioRegisters()
        self.clearRDSinfo()
        
    def getChannel(self):
        self.readRadioRegisters()
        self.getRegister0BhReadChannel()
        return ((self.CHANNEL))

    def getAllChannel(self):
        channel = self.FIRSTCHANNEL
        oldChannel = channel
        self.setChannel(channel)
        while True:
            self.radioSeek(self.HIGH)
            self.readRadioRegisters()
            self.getRegister0AhStatusRSSI()
            self.getRegister0BhReadChannel()
                
            if (self.CHANNEL >= self.LASTCHANNEL) :
                self.setChannel(oldChannel)
                break
            oldChannel  = self.CHANNEL
            if (self.SFBL == self.LOW):
                print (("  "+str(self.CHANNEL/10))[-5:] + " MHz - RSSI: " + str(self.RSSI) ) #+ " - " + self.getRdsProgramService(10000))

    def getProgramService(self):
        if(chr(0) in self.ProgrammeService and self.SFBL == self.LOW and self.RSSI >= 35):
            startTime = time.ticks_ms()
            while True:
                if(time.ticks_ms() - startTime > 5000) :break
                if(chr(0) not in self.ProgrammeService):break
                time.sleep_ms(50)
                self.getRDS(0,0, "0A", 1)

        resultString = ""
        for x in self.ProgrammeService:
            if (32 <= ord(x) < 126):
                resultString += x
            else :
                resultString += " "
        return resultString
    
    def setVolume(self,volume):
        self.readRadioRegisters()
        if(volume < 0): volume = 0
        if(volume > 15): volume = 15
        #VOLUME (05h.3:0)—Volume
        self.radioRegister[0x05] &= ~(0b1111)
        self.radioRegister[0x05] |= volume
        self.writeRadioRegisters()

    def getVolume(self):
        self.readRadioRegisters()
        self.getRegister05hSysConfig2()
        return (self.VOLUME)

    def getRSSI(self):
        self.readRadioRegisters()
        self.getRegister0AhStatusRSSI()
        return self.RSSI

    def getRdsPTY(self):
        if   (self.PTY==31):PTY = "ALARM"
        elif (self.PTY==30):PTY = "TEST ALARM"
        elif (self.PTY== 8):PTY = "Science"
        elif (self.PTY==10):PTY = "Popular Music"
        elif (self.PTY==11):PTY = "Rock Music"
        elif (self.PTY==12):PTY = "Easy Listening"
        elif (self.PTY==14):PTY = "Serious Classical"
        else: PTY = str(self.PTY)
        print ("PTY        : " + PTY)
        
    def getRdsPi(self):
        #EN50067_RDS_Standard.pdf
        #rds-koder-i-det-svenska-fm-natet2.pdf
        
        if (self.PiCountry==0xe):PiCountry = "Sweden"
        else: PiCountry = str(hex(self.PiCountry)[2:])
        print ("PI Country : " + PiCountry)
        
        if (self.PiCountry==0x0):PiType = "Local"
        elif (self.PiCountry==0x1):PiType = "International"
        elif (self.PiCountry==0x2):PiType = "National"
        elif (self.PiCountry==0x3):PiType = "Supra-regional"
        else:PiType = "Regional: "+str(self.PiCountry-3)
        print ("PI Type    : " + PiType)
        
        if    (self.PiReferens==0x01):PiReferens="SR P1"
        elif  (self.PiReferens==0x02):PiReferens="SR P2"
        elif  (self.PiReferens==0x03):PiReferens="SR P3"
        elif  (self.PiReferens==0x24):PiReferens="SR P4"
        elif  (self.PiReferens==0x41):PiReferens="Rix FM"
        elif  (self.PiReferens==0x43):PiReferens="Mix Megapol"
        elif  (self.PiReferens==0xA0):PiReferens="Rockklassiker"
        else:PiReferens=str(hex(self.PiReferens)[2:])
        print ("PI Referens: " + PiReferens)

    def getRegister00hDeviceID(self):
        # Si4702-03-C19-1.pdf
        # Register00h. Device ID

        #Part Number.
        PN_Mask   = 0b1111000000000000
        PN_Offset = 12
        self.PN = (self.radioRegister[0x00] & PN_Mask) >> PN_Offset

        #Manufacturer ID.
        MFGID_Mask    = 0b0000111111111111
        MFGID_Offset  = 0
        self.MFGID = (self.radioRegister[0x00] & MFGID_Mask) >> MFGID_Offset
        
    def getRegister01hChipID(self):
        # Si4702-03-C19-1.pdf
        # Register01h. Chip ID
        
        #Chip Version.
        REV_Mask   = 0b1111110000000000
        REV_Offset = 10
        self.REV = (self.radioRegister[0x01] & REV_Mask) >> REV_Offset

        #Device.
        DEV_Mask    = 0b0000001111000000
        DEV_Offset  = 6
        self.DEV = (self.radioRegister[0x01] & DEV_Mask) >> DEV_Offset

        #Firmware Version.
        FIRMWARE_Mask    = 0b0000000000111111
        FIRMWARE_Offset  = 0
        self.FIRMWARE = (self.radioRegister[0x01] & FIRMWARE_Mask) >> FIRMWARE_Offset        

    def getRegister02hPowerConfiguration(self):
        # Si4702-03-C19-1.pdf
        # Register02h. Power Configuration

        #Softmute Disable.
        DSMUTE_Mask   = 0b1000000000000000
        DSMUTE_Offset = 15
        self.DSMUTE = (self.radioRegister[0x02] & DSMUTE_Mask) >> DSMUTE_Offset

        #Mute Disable.
        DMUTE_Mask    = 0b0100000000000000
        DMUTE_Offset  = 14
        self.DMUTE = (self.radioRegister[0x02] & DMUTE_Mask) >> DMUTE_Offset

        #Mono Select
        MONO_Mask    = 0b0010000000000000
        MONO_Offset  = 13
        self.MONO = (self.radioRegister[0x02] & MONO_Mask) >> MONO_Offset

        #RDS Mode.
        RDSM_Mask    = 0b0000100000000000
        RDSM_Offset  = 11
        self.RDSM = (self.radioRegister[0x02] & RDSM_Mask) >> RDSM_Offset

        #Seek Mode.
        SKMODE_Mask    = 0b0000010000000000
        SKMODE_Offset  = 10
        self.SKMODE = (self.radioRegister[0x02] & SKMODE_Mask) >> SKMODE_Offset

        #Seek Direction.
        SEEKUP_Mask    = 0b0000001000000000
        SEEKUP_Offset  = 9
        self.SEEKUP = (self.radioRegister[0x02] & SEEKUP_Mask) >> SEEKUP_Offset

        #Seek.
        SEEK_Mask    = 0b0000000100000000
        SEEK_Offset  = 8
        self.SEEK = (self.radioRegister[0x02] & SEEK_Mask) >> SEEK_Offset

        #powerUp Disable.
        DISABLE_Mask    = 0b0000000001000000
        DISABLE_Offset  = 6
        self.DISABLE = (self.radioRegister[0x02] & DISABLE_Mask) >> DISABLE_Offset

        #powerUp Enable.
        ENABLE_Mask    = 0b0000000000000001
        ENABLE_Offset  = 0
        self.ENABLE = (self.radioRegister[0x02] & ENABLE_Mask) >> ENABLE_Offset

    def getRegister03hChannel(self):
        #USE getRegister0BhReadChannel
        #ReadChannel provides the current tuned channel and is updated during a seek operation
        NULL

    def getRegister04hSysConfig1(self):
        # Register04h. System Configuration 1
        
        #RDSIEN - RDS Interrupt Enable
        #Setting RDSIEN = 1 and GPIO2[1:0] = 01 will generate a 5ms low pulse on GPIO2 when the RDSR 0Ah[15] bit is set.
        RDSIEN_Mask   = 0b1000000000000000
        RDSIEN_Offset = 15
        self.RDSIEN = (self.radioRegister[0x04] & RDSIEN_Mask) >> RDSIEN_Offset
        
        #STCIEN -  Seek/Tune Complete Interrupt Enable
        #Setting STCIEN = 1 and GPIO2[1:0]=01 will generate a 5ms low pulse on GPIO2 when the STC 0Ah[14] bit is set
        STCIEN_Mask   = 0b0100000000000000
        STCIEN_Offset = 14
        self.STCIEN = (self.radioRegister[0x04] & STCIEN_Mask) >> STCIEN_Offset
        
        #RDS - RDS Enable
        RDS_Mask   = 0b0001000000000000
        RDS_Offset = 12
        self.RDS = (self.radioRegister[0x04] & RDS_Mask) >> RDS_Offset

        #DE - De-emphasis
        #0 = 75 µs. Used in USA (default).
        #1 = 50 µs. Used in Europe, Australia, Japan.
        DE_Mask   = 0b0000100000000000
        DE_Offset = 11
        self.DE = (self.radioRegister[0x04] & DE_Mask) >> DE_Offset

        #AGCD - AGC Disable
        AGCD_Mask   = 0b0000010000000000
        AGCD_Offset = 10
        self.AGCD = (self.radioRegister[0x04] & AGCD_Mask) >> AGCD_Offset

        #BLNDADJ -  Stereo/Mono Blend Level Adjustment
        #10=19–37 RSSI dBµV (–12dB).
        #11=25–43 RSSI dBµV (–6dB).
        #00=31–49 RSSI dBµV (default).
        #01=37–55 RSSI dBµV (+6dB).
        #ST bit set for RSSI values greater than low end of range.
        BLNDADJ_Mask   = 0b0000000011000000
        BLNDADJ_Offset = 6
        self.BLNDADJ = (self.radioRegister[0x04] & BLNDADJ_Mask) >> BLNDADJ_Offset

        #GPIO3 - General Purpose I/O 3
        GPIO3_Mask   = 0b0000000000110000
        GPIO3_Offset = 4
        self.GPIO3 = (self.radioRegister[0x04] & GPIO3_Mask) >> GPIO3_Offset

        #GPIO2 - General Purpose I/O 2
        GPIO2_Mask   = 0b0000000000001100
        GPIO2_Offset = 2
        self.GPIO2 = (self.radioRegister[0x04] & GPIO2_Mask) >> GPIO2_Offset

        #GPIO1 - General Purpose I/O 1
        GPIO1_Mask   = 0b0000000000000011
        GPIO1_Offset = 0
        self.GPIO1 = (self.radioRegister[0x04] & GPIO1_Mask) >> GPIO1_Offset

    def getRegister05hSysConfig2(self):
        # Register05h. System Configuration 2

        #RSSI Seek Threshold
        SEEKTH_Mask   = 0b1111111100000000
        SEEKTH_Offset = 8
        self.SEEKTH = (self.radioRegister[0x05] & SEEKTH_Mask) >> SEEKTH_Offset

        #Band Select
        BAND_Mask   = 0b0000000011000000
        BAND_Offset = 6
        self.BAND = (self.radioRegister[0x05] & BAND_Mask) >> BAND_Offset

        #Channel Spacing
        SPACE_Mask   = 0b0000000000110000
        SPACE_Offset = 4
        self.SPACE = (self.radioRegister[0x05] & SPACE_Mask) >> SPACE_Offset

        #Volume
        VOLUME_Mask   = 0b0000000000001111
        VOLUME_Offset = 0
        self.VOLUME = (self.radioRegister[0x05] & VOLUME_Mask) >> VOLUME_Offset

    def getRegister06hSysConfig3(self):
        # Register06h. System Configuration 3

        #SMUTER - Softmute Attack/Recover Rate
        SMUTER_Mask   = 0b1100000000000000
        SMUTER_Offset = 14
        self.SMUTER = (self.radioRegister[0x06] & SMUTER_Mask) >> SMUTER_Offset

        #SMUTEA - Softmute Attenuation
        SMUTEA_Mask   = 0b0011000000000000
        SMUTEA_Offset = 12
        self.SMUTEA = (self.radioRegister[0x06] & SMUTEA_Mask) >> SMUTEA_Offset

        #VOLEXT - Extended Volume Range
        VOLEXT_Mask   = 0b0000000100000000
        VOLEXT_Offset = 8
        self.VOLEXT = (self.radioRegister[0x06] & VOLEXT_Mask) >> VOLEXT_Offset

        #SKSNR - Seek SNR Threshold
        SKSNR_Mask   = 0b0000000011110000
        SKSNR_Offset = 4
        self.SKSNR = (self.radioRegister[0x06] & SKSNR_Mask) >> SKSNR_Offset

        #SKCNT - Seek FM Impulse Detection Threshold.
        SKCNT_Mask   = 0b0000000000001111
        SKCNT_Offset = 0
        self.SKCNT = (self.radioRegister[0x06] & SKCNT_Mask) >> SKCNT_Offset

    def getRegister07hTest1(self):
        # Register07h. Test 1

        #XOSCEN - Crystal Oscillator Enable
        XOSCEN_Mask   = 0b1000000000000000
        XOSCEN_Offset = 15
        self.XOSCEN = (self.radioRegister[0x06] & XOSCEN_Mask) >> XOSCEN_Offset

        #AHIZEN - Audio High-Z Enable
        AHIZEN_Mask   = 0b0100000000000000
        AHIZEN_Offset = 14
        self.AHIZEN = (self.radioRegister[0x06] & AHIZEN_Mask) >> AHIZEN_Offset

    def getRegister0AhStatusRSSI(self):
        # Si4702-03-C19-1.pdf
        # Register0Ah. Status RSSI
        # RSSI (Received Signal Strength Indicator).
        # RSSI is measured units of dBµV in 1 dB increments with a maximum of approximately 
        # 75 dBµV. Si4702/03-C19 does not report RSSI levels greater than 75 dBuV

        #RDS Ready
        RDSR_Mask   = 0b1000000000000000
        RDSR_Offset = 15
        self.RDSR = (self.radioRegister[0x0A] & RDSR_Mask) >> RDSR_Offset

        #Seek/Tune Complete
        STC_Mask    = 0b0100000000000000
        STC_Offset  = 14
        self.STC = (self.radioRegister[0x0A] & STC_Mask) >> STC_Offset

        #Seek Fail/Band Limit
        SFBL_Mask   = 0b0010000000000000
        SFBL_Offset = 13
        self.SFBL = (self.radioRegister[0x0A] & SFBL_Mask) >> SFBL_Offset

        #AFC Rail
        AFCRL_Mask  = 0b0001000000000000
        AFCRL_Offset= 12
        self.AFCRL = (self.radioRegister[0x0A] & AFCRL_Mask) >> AFCRL_Offset

        #RDS Synchronized.
        RDSS_Mask   = 0b0000100000000000
        RDSS_Offset = 11
        self.RDSS = (self.radioRegister[0x0A] & RDSS_Mask) >> RDSS_Offset

        #RDS Block A Errors
        BLERA_Mask  = 0b0000011000000000
        BLERA_Offset= 9
        self.BLERA = (self.radioRegister[0x0A] & BLERA_Mask) >> BLERA_Offset

        #Stereo Indicator
        ST_Mask     = 0b0000000100000000
        ST_Offset   = 8
        self.ST = (self.radioRegister[0x0A] & ST_Mask) >> ST_Offset

        #RSSI (Received Signal Strength Indicator)
        RSSI_Mask   = 0b0000000011111111
        RSSI_Offset = 0
        self.RSSI = (self.radioRegister[0x0A] & RSSI_Mask) >> RSSI_Offset

    def getRegister0BhReadChannel(self):
        # Si4702-03-C19-1.pdf
        # Register0Bh. READCHAN

        #RDS Block B Errors
        BLERB_Mask  = 0b1100000000000000
        BLERB_Offset= 14
        self.BLERB = (self.radioRegister[0x0B] & BLERB_Mask) >> BLERB_Offset

        #RDS Block C Errors
        BLERC_Mask  = 0b0011000000000000
        BLERC_Offset= 12
        self.BLERC = (self.radioRegister[0x0B] & BLERC_Mask) >> BLERC_Offset

        #RDS Block D Errors
        BLERD_Mask  = 0b0000110000000000
        BLERD_Offset= 10
        self.BLERD = (self.radioRegister[0x0B] & BLERD_Mask) >> BLERD_Offset

        #CHANNEL
        CHANNEL_Mask= 0b0000001111111111
        CHANNEL_Offset = 0
        self.CHANNEL = ((self.radioRegister[0x0B] & CHANNEL_Mask) >> CHANNEL_Offset) + self.FIRSTCHANNEL

    def viewRadioRegisters(self):
        self.readRadioRegisters()
        print("DEVICEID =   " + ("0000000000000000" + str(bin(self.radioRegister[0x00])[2:]))[-16:])
        print("CHIPID =     " + ("0000000000000000" + str(bin(self.radioRegister[0x01])[2:]))[-16:])
        print("POWERCFG =   " + ("0000000000000000" + str(bin(self.radioRegister[0x02])[2:]))[-16:])
        print("CHANNEL =    " + ("0000000000000000" + str(bin(self.radioRegister[0x03])[2:]))[-16:])
        print("SYSCONFIG1 = " + ("0000000000000000" + str(bin(self.radioRegister[0x04])[2:]))[-16:])
        print("SYSCONFIG2 = " + ("0000000000000000" + str(bin(self.radioRegister[0x05])[2:]))[-16:])
        print("SYSCONFIG3 = " + ("0000000000000000" + str(bin(self.radioRegister[0x06])[2:]))[-16:])
        print("TEST1 =      " + ("0000000000000000" + str(bin(self.radioRegister[0x07])[2:]))[-16:])
        print("TEST2 =      " + ("0000000000000000" + str(bin(self.radioRegister[0x08])[2:]))[-16:])
        print("BOOTCONFIG = " + ("0000000000000000" + str(bin(self.radioRegister[0x09])[2:]))[-16:])
        print("STATUSRSSI = " + ("0000000000000000" + str(bin(self.radioRegister[0x0A])[2:]))[-16:])
        print("READCHAN =   " + ("0000000000000000" + str(bin(self.radioRegister[0x0B])[2:]))[-16:])
        print("RDSA =       " + ("0000000000000000" + str(bin(self.radioRegister[0x0C])[2:]))[-16:])
        print("RDSB =       " + ("0000000000000000" + str(bin(self.radioRegister[0x0D])[2:]))[-16:])
        print("RDSC =       " + ("0000000000000000" + str(bin(self.radioRegister[0x0E])[2:]))[-16:])
        print("RDSD =       " + ("0000000000000000" + str(bin(self.radioRegister[0x0F])[2:]))[-16:])
        return self.radioRegister

    def getSomeMessagesRDS(self, sleep = 50, maxTime = 5000, FindNew = 0, FilterGroup="", silent=0):    
        startTime = time.ticks_ms()
        while True:
            if(time.ticks_ms() - startTime > maxTime) :
                break
            time.sleep_ms(sleep)
            self.getRDS(0,FindNew, FilterGroup, silent)

    def getRDS(self, debug=1, FindNew=0, FilterGroup="", silent=0):    
        #3.1.4.2 Open Data Applications - Group structure
        startTime = time.ticks_ms()
        maxTime   = 1000
        while True:
            self.readRadioRegisters()
            self.getRegister0AhStatusRSSI()
            if(self.RDSR == self.HIGH):break
            if(time.ticks_ms() - startTime > maxTime) :break
            time.sleep_ms(50)
            
        if(self.RDSR == self.HIGH):
            #read group type

            GroupType_Mask     = 0b1111000000000000
            GroupType_Offset   = 12
            GroupFormat_Mask   = 0b0000100000000000
            GroupFormat_Offset = 11
            TP_Mask            = 0b0000010000000000
            TP_Offset          = 10
            PTY_Mask           = 0b0000001111100000
            PTY_Offset         = 5
            
            PI_Country_Mask    = 0b1111000000000000
            PI_Country_Offset  = 12
            PI_Type_Mask       = 0b0000111100000000
            PI_Type_Offset     = 8
            PI_Referens_Mask   = 0b0000000011111111

            groupType = str((self.radioRegister[self.RDSB] & GroupType_Mask) >> GroupType_Offset) + chr(((self.radioRegister[self.RDSB] & GroupFormat_Mask) >> GroupFormat_Offset)+65)
            self.TP         = (self.radioRegister[self.RDSB] & TP_Mask) >> TP_Offset
            self.PTY        = (self.radioRegister[self.RDSB] & PTY_Mask) >> PTY_Offset
            self.PiCountry  = (self.radioRegister[self.RDSA] & PI_Country_Mask) >> PI_Country_Offset
            self.PiType     = (self.radioRegister[self.RDSA] & PI_Type_Mask) >> PI_Type_Offset
            self.PiReferens = (self.radioRegister[self.RDSA] & PI_Referens_Mask)

            if (debug==1):
                print ("GroupType  : " + groupType)
                print ("TP         : " + hex(self.TP)[2:])
                self.getRdsPTY()
                self.getRdsPi()
            
            if (FindNew == 0 or FilterGroup != ""):
                if   (FilterGroup in ("","0A") and groupType == "0A"): self.rdsGroupType0A(silent)   #3.1.5.1 Type 0 groups: Basic tuning and switching information
                elif (FilterGroup in ("","1A") and groupType == "1A"): self.rdsGroupType1("A",silent)   #3.1.5.2 Type 1 groups: Programme Item Number and slow labelling codes
                elif (FilterGroup in ("","1B") and groupType == "1B"): self.rdsGroupType1("B",silent)   #3.1.5.2 Type 1 groups: Programme Item Number and slow labelling codes
                elif (FilterGroup in ("","2A") and groupType == "2A"): self.rdsGroupType2A(silent)   #3.1.5.3 Type 2 groups: RadioText
                elif (FilterGroup in ("","3A") and groupType == "3A"): self.rdsGroupType3A(silent)   #3.1.5.4 Type 3A groups: Application identification for Open data
                elif (FilterGroup in ("","4A") and groupType == "4A"): self.rdsGroupType4A(silent)   #3.1.5.6 Type 4A groups : Clock-time and date
                elif (FilterGroup in ("","7A") and groupType == "7A"): self.rdsGroupType7A(silent)   #3.1.5.10 Type 7A groups: Radio Paging or ODA
                elif (FilterGroup in ("","10A") and groupType == "10A"): self.rdsGroupType10A(silent) #3.1.5.14 Type 10 groups: Programme Type Name (Group type 10A) and Open data (Group type 10B)
                elif (FilterGroup in ("","14A") and groupType == "14A"): self.rdsGroupType14A(silent) #3.1.5.19 Type 14 groups: Enhanced Other Networks information
                elif (FilterGroup == "" or FilterGroup == groupType):
                    print ("GroupType  : " + groupType)
                    print ("RDSA Bin : " + str(bin(self.radioRegister[self.RDSA])))
                    print ("RDSB Bin : " + str(bin(self.radioRegister[self.RDSB])))
                    print ("RDSC Bin : " + str(bin(self.radioRegister[self.RDSC])))
                    print ("RDSD Bin : " + str(bin(self.radioRegister[self.RDSD])))
                
            if (FindNew == 1 and groupType in ("5A","6A","8A","9A","11A","12A","13A","15A","0B","2B","3B","4B","5B","6B","7B","8B","9B","10B","11B","12B","13B","14B","15B")): 
                print ("GroupType  : " + groupType)
                print ("RDSA Bin : " + str(bin(self.radioRegister[self.RDSA])))
                print ("RDSB Bin : " + str(bin(self.radioRegister[self.RDSB])))
                print ("RDSC Bin : " + str(bin(self.radioRegister[self.RDSC])))
                print ("RDSD Bin : " + str(bin(self.radioRegister[self.RDSD])))

            silent = self.HIGH
            if (FilterGroup != ""):
                if   (groupType == "0A"): self.rdsGroupType0A(silent)   #3.1.5.1 Type 0 groups: Basic tuning and switching information
                elif (groupType == "1A"): self.rdsGroupType1("A",silent)   #3.1.5.2 Type 1 groups: Programme Item Number and slow labelling codes
                elif (groupType == "1B"): self.rdsGroupType1("B",silent)   #3.1.5.2 Type 1 groups: Programme Item Number and slow labelling codes
                elif (groupType == "2A"): self.rdsGroupType2A(silent)   #3.1.5.3 Type 2 groups: RadioText
                elif (groupType == "3A"): self.rdsGroupType3A(silent)   #3.1.5.4 Type 3A groups: Application identification for Open data
                elif (groupType == "4A"): self.rdsGroupType4A(silent)   #3.1.5.6 Type 4A groups : Clock-time and date
                elif (groupType == "7A"): self.rdsGroupType7A(silent)   #3.1.5.10 Type 7A groups: Radio Paging or ODA
                elif (groupType == "10A"): self.rdsGroupType10A(silent) #3.1.5.14 Type 10 groups: Programme Type Name (Group type 10A) and Open data (Group type 10B)
                elif (groupType == "14A"): self.rdsGroupType14A(silent) #3.1.5.19 Type 14 groups: Enhanced Other Networks information            

    def rdsGroupType0A(self, silent = 0):
        if (silent == 0):
            print()
            print ("3.1.5.1 Type 0 groups: Basic tuning and switching information")
        # Programme Service
        DI_Mask              = 0b0000000000000100
        DI_RightShift        = 2
        MS_Mask              = 0b0000000000001000
        MS_RightShift        = 3
        TA_Mask              = 0b0000000000010000
        TA_RightShift        = 4
        PSIndex_Mask         = 0b0000000000000011
        PSIndex_RightShift   = 0
        PSCharA_Mask         = 0b1111111100000000
        PSCharA_RightShift   = 8
        PSCharB_Mask         = 0b0000000011111111
        PSCharB_RightShift   = 0
        
        ProgrammeServiceIndex = (self.radioRegister[self.RDSB] & PSIndex_Mask) >> PSIndex_RightShift
        ProgrammeCharA = chr((self.radioRegister[self.RDSD] & PSCharA_Mask) >> PSCharA_RightShift)
        ProgrammeCharB = chr((self.radioRegister[self.RDSD] & PSCharB_Mask) >> PSCharB_RightShift)
        DI = (self.radioRegister[self.RDSB] & DI_Mask) >> DI_RightShift
        MS = (self.radioRegister[self.RDSB] & MS_Mask) >> MS_RightShift
        self.TA = (self.radioRegister[self.RDSB] & TA_Mask) >> TA_RightShift
        
        if    (self.TP==0 and self.TA==0):TPTA="No TA" #This program does not carry traffic announcements nor does it refer, via EON, to a program that does.
        elif  (self.TP==0 and self.TA==1):TPTA="EON" #This program carries EON information about another program which gives traffic information.
        elif  (self.TP==1 and self.TA==0):TPTA="TA & EON" #This program carries traffic announcements but none are being broadcast at present.
        elif  (self.TP==1 and self.TA==1):TPTA="Active" #A traffic announcement is being broadcast on this program at present.
        
        if (silent == 0):
            print ("DI : " + str(DI) + ", MS : " + str(MS) + ", TA : " + TPTA + ", Index : " + str(ProgrammeServiceIndex) + " [" + ProgrammeCharA + ":" + ProgrammeCharB + "]")
            
        self.ProgrammeService[ProgrammeServiceIndex * 2 + 0] = ProgrammeCharA
        self.ProgrammeService[ProgrammeServiceIndex * 2 + 1] = ProgrammeCharB
        
        PS = ""
        for x in self.ProgrammeService:
            if (32 <= ord(x) < 126): PS += x
            else: PS += " "

        if (silent == 0):
            print ("ProgrammeService : " + PS)

        AltFreqA_Mask        = 0b1111111100000000
        AltFreqA_RightShift  = 8
        AltFreqB_Mask        = 0b0000000011111111
        AltFreqB_RightShift  = 0

        AltFreqA = (((self.radioRegister[self.RDSC] & AltFreqA_Mask) >> AltFreqA_RightShift)+875)/10
        AltFreqB = (((self.radioRegister[self.RDSC] & AltFreqB_Mask) >> AltFreqB_RightShift)+875)/10

        if (silent == 0):
            print ("Alt. freq. A: " + str(AltFreqA))                
            print ("Alt. freq. B: " + str(AltFreqB))                

    def rdsGroupType1(self,char, silent = 0):
        if (silent == 0):
            print()
            print ("3.1.5.2 Type 1 groups: Programme Item Number and slow labelling codes")
        # Programme item number code
        PinDay_Mask          = 0b1111100000000000
        PinDay_RightShift    = 11
        PinHour_Mask         = 0b0000011111000000
        PinHour_RightShift   = 6
        PinMinute_Mask       = 0b0000000000111111
        PinMinute_RightShift = 0
        
        PinDay    = (self.radioRegister[self.RDSD] & PinDay_Mask) >> PinDay_RightShift
        PinHour   = (self.radioRegister[self.RDSD] & PinHour_Mask) >> PinHour_RightShift
        PinMinute = (self.radioRegister[self.RDSD] & PinMinute_Mask) >> PinMinute_RightShift
        Pin       = ("0"+str(PinDay))[-2:] + ("0"+str(PinHour))[-2:] + ("0"+str(PinMinute))[-2:]        
        
        #Radio Paging Codes
        RPC_Mask       = 0b0000000000011111
        RPC_RightShift = 0
        
        RPC    = (self.radioRegister[self.RDSB] & RPC_Mask) >> RPC_RightShift
        if (char == "B"):
            if (silent == 0):
                print ("Programme item number code : " + Pin)
        else:   
            #Slow labelling codes
            LinkageActuator_Mask           = 0b1000000000000000
            LinkageActuator_RightShift     = 15
            VariantCode_Mask               = 0b0111000000000000
            VariantCode_RightShift         = 12
            Paging_Mask                    = 0b0000111100000000
            Paging_RightShift              = 8
            ExtendedCountryCode_Mask       = 0b0000000011111111
            ExtendedCountryCode_RightShift = 0
            Other_Mask                     = 0b0000111111111111
            Other_RightShift               = 0
            
            LinkageActuator           = (self.radioRegister[self.RDSC] & LinkageActuator_Mask) >> LinkageActuator_RightShift
            VariantCode               = (self.radioRegister[self.RDSC] & VariantCode_Mask) >> VariantCode_RightShift
            Paging                    = (self.radioRegister[self.RDSC] & Paging_Mask) >> Paging_RightShift
            ExtendedCountryCode       = (self.radioRegister[self.RDSC] & ExtendedCountryCode_Mask) >> ExtendedCountryCode_RightShift
            Other                     = (self.radioRegister[self.RDSC] & Other_Mask) >> Other_RightShift
            
            PI_Country_Mask    = 0b1111000000000000
            PI_Country_Offset  = 12
            PI_Country         = (self.radioRegister[self.RDSA] & PI_Country_Mask) >> PI_Country_Offset
            
            if (silent == 0):
                print ("Programme item number code : " + Pin + " Radio Paging Codes: " + str(RPC) + " LinkageActuator: " + str(LinkageActuator) + " VariantCode: " + str(VariantCode))
            
                if  (VariantCode == 0b000 and ExtendedCountryCode == 0xE3 and PI_Country == 0x0E):print ("ExtendedCountryCode: Sweden")
                elif(VariantCode == 0b000):print ("Paging: " + str(Paging) + " ExtendedCountryCode: " + str(ExtendedCountryCode))
                elif(VariantCode == 0b001):print ("TMC identification: " + str(Other) )
                elif(VariantCode == 0b010):print ("Paging identification: " + str(Other) )
                elif(VariantCode == 0b011 and Other == 0x28):print ("Language codes: Swedish" )
                elif(VariantCode == 0b011):print ("Language codes: " + str(hex(Other)) )
                elif(VariantCode == 0b100):print ("not assigned: " + str(Other) )
                elif(VariantCode == 0b101):print ("not assigned: " + str(Other) )
                elif(VariantCode == 0b110):print ("For use by broadcasters: " + str(Other) )
                elif(VariantCode == 0b111):print ("Identification of EWS channel: " + str(Other) )
            
    def rdsGroupType2A(self, silent = 0):
        if (silent == 0):
            print()
            print ("3.1.5.3 Type 2 groups: RadioText")
        RT_index_Mask         = 0b0000000000001111
        RT_index_RightShift   = 0
        RT_flag_Mask          = 0b0000000000010000
        RT_flag_RightShift    = 4
        RT_CharA_Mask         = 0b1111111100000000
        RT_CharA_RightShift   = 8
        RT_CharB_Mask         = 0b0000000011111111
        RT_CharB_RightShift   = 0
        RT_CharC_Mask         = 0b1111111100000000
        RT_CharC_RightShift   = 8
        RT_CharD_Mask         = 0b0000000011111111
        RT_CharD_RightShift   = 0

        RT_index = (self.radioRegister[self.RDSB] & RT_index_Mask) >> RT_index_RightShift
        RT_flag  = (self.radioRegister[self.RDSB] & RT_flag_Mask) >> RT_flag_RightShift
        RT_CharA = chr((self.radioRegister[self.RDSC] & RT_CharA_Mask) >> RT_CharA_RightShift)
        RT_CharB = chr((self.radioRegister[self.RDSC] & RT_CharB_Mask) >> RT_CharB_RightShift)
        RT_CharC = chr((self.radioRegister[self.RDSD] & RT_CharC_Mask) >> RT_CharC_RightShift)
        RT_CharD = chr((self.radioRegister[self.RDSD] & RT_CharD_Mask) >> RT_CharD_RightShift)

        if (silent == 0):
            print ("RT_flag: " + str(RT_flag) + ", RT_index: " + str(RT_index) + " " + RT_CharA+RT_CharB+RT_CharC+RT_CharD)

        if(RT_flag == 0):
            if(self.RadioTextFlag==1):self.RadioTextA = [chr(0)] * 64
            self.RadioTextA[RT_index * 4 + 0] = RT_CharA
            self.RadioTextA[RT_index * 4 + 1] = RT_CharB
            self.RadioTextA[RT_index * 4 + 2] = RT_CharC
            self.RadioTextA[RT_index * 4 + 3] = RT_CharD
        else:
            if(self.RadioTextFlag==0):self.RadioTextB = [chr(0)] * 64
            self.RadioTextB[RT_index * 4 + 0] = RT_CharA
            self.RadioTextB[RT_index * 4 + 1] = RT_CharB
            self.RadioTextB[RT_index * 4 + 2] = RT_CharC
            self.RadioTextB[RT_index * 4 + 3] = RT_CharD

        self.RadioTextFlag = RT_flag

        RTA = ""
        RTB = ""
        for x in self.RadioTextA:
            if (32 <= ord(x) < 126): RTA += x
            else: RTA += " "
            #print (str(ord(x)))

        for x in self.RadioTextB:
            if (32 <= ord(x) < 126): RTB += x
            else: RTB += " "

        if (silent == 0):
            print ("RadioTextA : " + RTA)
            print ("RadioTextB : " + RTB)

    def rdsGroupType3A(self, silent = 0):
        if (silent == 0):
            print()
            print ("3.1.5.4 Type 3A groups: Application identification for Open data")
        # Programme Service
        Type_Mask            = 0b0000000000011111
        Type_RightShift      = 0
        Message_Mask         = 0b1111111111111111
        Message_RightShift   = 0
        ID_Mask              = 0b1111111111111111
        ID_RightShift        = 0
        
        ApplicationGroupTypeCode  = (self.radioRegister[self.RDSB] & Type_Mask) >> Type_RightShift
        MessageBits               = (self.radioRegister[self.RDSC] & Message_Mask) >> Message_RightShift
        ApplicationIdentification = (self.radioRegister[self.RDSD] & ID_Mask) >> ID_RightShift
        
        if (silent == 0):
            print ("ApplicationGroupType : " + str(ApplicationGroupTypeCode) + ", MessageBits : " + str(MessageBits) + ", AID: " + str(ApplicationIdentification))

    def rdsGroupType4A(self, silent = 0):
        if (silent == 0):
            print()
            print ("3.1.5.6 Type 4A groups : Clock-time and date")

        LocalTimeOffset_Mask         = 0b0000000000011111
        LocalTimeOffset_RightShift   = 0
        LocalTimeSense_Mask          = 0b0000000000100000
        LocalTimeSense_RightShift    = 5

        LocalTimeOffsetHour      = ((self.radioRegister[self.RDSD] & LocalTimeOffset_Mask) >> LocalTimeOffset_RightShift) / 2.0
        if(((self.radioRegister[self.RDSD] & LocalTimeSense_Mask) >> LocalTimeSense_RightShift) == 1):
            LocalTimeOffsetHour = LocalTimeOffsetHour * -1

        UtcMinute_Mask               = 0b0000111111000000
        UtcMinute_RightShift         = 6
        UtcHourPartLow_Mask          = 0b1111000000000000
        UtcHourPartLow_RightShift    = 12
        UtcHourPartHigh_Mask         = 0b0000000000000001
        UtcHourPartHigh_LeftShift    = 4
        
        UtcMinute = (self.radioRegister[self.RDSD] & UtcMinute_Mask) >> UtcMinute_RightShift
        UtcHour   = ((self.radioRegister[self.RDSD] & UtcHourPartLow_Mask) >> UtcHourPartLow_RightShift)+((self.radioRegister[self.RDSC] & UtcHourPartHigh_Mask) << UtcHourPartHigh_LeftShift)

        # Modified Julian Day Code
        MJDCodePartLow_Mask          = 0b1111111111111110
        MJDCodePartLow_RightShift    = 1
        MJDCodePartHigh_Mask         = 0b0000000000000011
        MJDCodePartHigh_LeftShift    = 15
        MJD = ((self.radioRegister[self.RDSC] & MJDCodePartLow_Mask) >> MJDCodePartLow_RightShift) + ((self.radioRegister[self.RDSB] & MJDCodePartHigh_Mask) << MJDCodePartHigh_LeftShift)
        MJD_YearPart = int((MJD - 15078.2) / 365.25 )
        MJD_MonthPart = int((MJD - 14956.1 - int(MJD_YearPart * 365.25) ) / 30.6001)
        MJD_Day = MJD - 14956 - int(MJD_YearPart * 365.25 ) - int( MJD_MonthPart * 30.6001)
        MJD_Month = MJD_MonthPart - 1
        MJD_Year  = MJD_YearPart + 1900
        if(MJD_MonthPart == 14 or MJD_MonthPart == 15):
            MJD_Year += 1
            MJD_Month -= 12
        MJD_WeekDay = (MJD + 2) % 7

        if (silent == 0):
            print ("MJD + UTC       : " + str(MJD_Year)+"-"+("0"+str(MJD_Month))[-2:]+"-"+("0"+str(MJD_Day))[-2:] + " " + ("0"+str(UtcHour))[-2:] +":"+ ("0"+str(UtcMinute))[-2:] + " TZ: " + str(LocalTimeOffsetHour))
        
        if(2000 <= MJD_Year <= 2099 and 1 <= MJD_Month <= 12 and 1 <= MJD_Day <= 31):
            rtc=RTC()
            # Set RTC
            # (year, month, mday, week_day, hours, minutes, seconds, sub-seconds)
            now = (MJD_Year,MJD_Month,MJD_Day,MJD_WeekDay,UtcHour,UtcMinute,0,0)
            rtc.datetime(now)
            
            year, month, day, hour, minute, second, weekday, yearday = time.gmtime(time.time() + int(LocalTimeOffsetHour * 3600))
            if (silent == 0):
                print ("RTC-localtime   : " + str(year)+"-"+("0"+str(month))[-2:]+"-"+("0"+str(day))[-2:]+ " " + ("0"+str(hour))[-2:] +":"+ ("0"+str(minute))[-2:] +":"+ ("0"+str(second))[-2:])

    def rdsGroupType7A(self, silent = 0):
        if (silent == 0):
            print()
            print ("3.1.5.10 Type 7A groups: Radio Paging or ODA")
        
        RP_index_Mask         = 0b0000000000001111
        RP_index_RightShift   = 0
        RP_flag_Mask          = 0b0000000000010000
        RP_flag_RightShift    = 4
        RP_CharA_Mask         = 0b1111111100000000
        RP_CharA_RightShift   = 8
        RP_CharB_Mask         = 0b0000000011111111
        RP_CharB_RightShift   = 0
        RP_CharC_Mask         = 0b1111111100000000
        RP_CharC_RightShift   = 8
        RP_CharD_Mask         = 0b0000000011111111
        RP_CharD_RightShift   = 0

        RP_index = (self.radioRegister[self.RDSB] & RP_index_Mask) >> RP_index_RightShift
        RP_flag  = (self.radioRegister[self.RDSB] & RP_flag_Mask) >> RP_flag_RightShift
        RP_CharA = chr((self.radioRegister[self.RDSC] & RP_CharA_Mask) >> RP_CharA_RightShift)
        RP_CharB = chr((self.radioRegister[self.RDSC] & RP_CharB_Mask) >> RP_CharB_RightShift)
        RP_CharC = chr((self.radioRegister[self.RDSD] & RP_CharC_Mask) >> RP_CharC_RightShift)
        RP_CharD = chr((self.radioRegister[self.RDSD] & RP_CharD_Mask) >> RP_CharD_RightShift)

        if (silent == 0):
            print ("RP_flag: " + str(RP_flag) + " RP_index: " + str(RP_index) + " " + RP_CharA+RP_CharB+RP_CharC+RP_CharD)

        if(RP_flag == 0):
            if(self.RadioPagingFlag==1):self.RadioPagingA = [chr(0)] * 64
            self.RadioPagingA[RP_index * 4 + 0] = RP_CharA
            self.RadioPagingA[RP_index * 4 + 1] = RP_CharB
            self.RadioPagingA[RP_index * 4 + 2] = RP_CharC
            self.RadioPagingA[RP_index * 4 + 3] = RP_CharD
        else:
            if(self.RadioPagingFlag==0):self.RadioPagingB = [chr(0)] * 64
            self.RadioPagingB[RP_index * 4 + 0] = RP_CharA
            self.RadioPagingB[RP_index * 4 + 1] = RP_CharB
            self.RadioPagingB[RP_index * 4 + 2] = RP_CharC
            self.RadioPagingB[RP_index * 4 + 3] = RP_CharD

        self.RadioPagingFlag = RP_flag

        RPA = ""
        RPB = ""
        for x in self.RadioPagingA:
            if (32 <= ord(x) < 126): RPA += x
            else: RPA += " "

        for x in self.RadioPagingB:
            if (32 <= ord(x) < 126): RPB += x
            else: RPB += " "

        if (silent == 0):
            print ("RadioPagingA : " + RPA)
            print ("RadioPagingB : " + RPB)

    def rdsGroupType10A(self, silent = 0):
        if (silent == 0):
            print()
            print ("3.1.5.14 Type 10 groups: Programme Type Name (Group type 10A) and Open data (Group type 10B)")
        
        # Programme Type Name
        PTYN_index_Mask         = 0b0000000000000001
        PTYN_index_RightShift   = 0
        PTYN_flag_Mask          = 0b0000000000010000
        PTYN_flag_RightShift    = 4
        PTYN_CharA_Mask         = 0b1111111100000000
        PTYN_CharA_RightShift   = 8
        PTYN_CharB_Mask         = 0b0000000011111111
        PTYN_CharB_RightShift   = 0
        PTYN_CharC_Mask         = 0b1111111100000000
        PTYN_CharC_RightShift   = 8
        PTYN_CharD_Mask         = 0b0000000011111111
        PTYN_CharD_RightShift   = 0

        PTYN_index = (self.radioRegister[self.RDSB] & PTYN_index_Mask) >> PTYN_index_RightShift
        PTYN_flag  = (self.radioRegister[self.RDSB] & PTYN_flag_Mask) >> PTYN_flag_RightShift
        PTYN_CharA = chr((self.radioRegister[self.RDSC] & PTYN_CharA_Mask) >> PTYN_CharA_RightShift)
        PTYN_CharB = chr((self.radioRegister[self.RDSC] & PTYN_CharB_Mask) >> PTYN_CharB_RightShift)
        PTYN_CharC = chr((self.radioRegister[self.RDSD] & PTYN_CharC_Mask) >> PTYN_CharC_RightShift)
        PTYN_CharD = chr((self.radioRegister[self.RDSD] & PTYN_CharD_Mask) >> PTYN_CharD_RightShift)

        if (silent == 0):
            print ("PTYN_flag: " + str(PTYN_flag) + ", PTYN_index: " + str(PTYN_index) + " " + PTYN_CharA+PTYN_CharB+PTYN_CharC+PTYN_CharD)

        if(PTYN_flag == 0):
            if(self.ProgrammeTypeNameFlag==1):self.ProgrammeTypeNameTextA = [chr(0)] * 8
            self.ProgrammeTypeNameTextA[PTYN_index * 4 + 0] = PTYN_CharA
            self.ProgrammeTypeNameTextA[PTYN_index * 4 + 1] = PTYN_CharB
            self.ProgrammeTypeNameTextA[PTYN_index * 4 + 2] = PTYN_CharC
            self.ProgrammeTypeNameTextA[PTYN_index * 4 + 3] = PTYN_CharD
        else:
            if(self.ProgrammeTypeNameFlag==0):self.ProgrammeTypeNameTextB = [chr(0)] * 8
            self.ProgrammeTypeNameTextB[PTYN_index * 4 + 0] = PTYN_CharA
            self.ProgrammeTypeNameTextB[PTYN_index * 4 + 1] = PTYN_CharB
            self.ProgrammeTypeNameTextB[PTYN_index * 4 + 2] = PTYN_CharC
            self.ProgrammeTypeNameTextB[PTYN_index * 4 + 3] = PTYN_CharD

        self.ProgrammeTypeNameFlag = PTYN_flag

        PTYNTextA = ""
        for x in self.ProgrammeTypeNameTextA:
            if (32 <= ord(x) < 126): PTYNTextA += x
            else: PTYNTextA += " "
            
        PTYNTextB = ""
        for x in self.ProgrammeTypeNameTextB:
            if (32 <= ord(x) < 126): PTYNTextB += x
            else: PTYNTextB += " "
            
        if (silent == 0):
            print ("ProgrammeTypeNameTextA : " + PTYNTextA)
            print ("ProgrammeTypeNameTextB : " + PTYNTextB)        

    def rdsGroupType14A(self, silent = 0):
        if (silent == 0):
            print()
            print("3.1.5.19 Type 14 groups: Enhanced Other Networks information")
        # Other Networks
        TP_Mask                = 0b0000000000010000
        TP_RightShift          = 4
        PI_Country_Mask        = 0b1111000000000000
        PI_Country_RightShift  = 12
        PI_Type_Mask           = 0b0000111100000000
        PI_Type_RightShift     = 8
        PI_Referens_Mask       = 0b0000000011111111
        PI_Referens_RightShift = 8
        
        TP         = (self.radioRegister[self.RDSB] & TP_Mask) >> TP_RightShift
        PiCountry  = (self.radioRegister[self.RDSD] & PI_Country_Mask) >> PI_Country_RightShift
        PiType     = (self.radioRegister[self.RDSD] & PI_Type_Mask) >> PI_Type_RightShift
        PiReferens = (self.radioRegister[self.RDSD] & PI_Referens_Mask) >> PI_Referens_RightShift

        if (silent == 0):
            print ("Other Networks TP:" + str(TP) + ", PiCountry: " + str(hex(PiCountry)[2:])  + ", PiType: " + str(PiType)  + ", PiReferens: " + str(PiReferens)) 
        
        VariantCode_Mask       = 0b0000000000001111
        VariantCode_RightShift = 0
        PartA_Mask             = 0b1111111100000000
        PartA_RightShift       = 8
        PartB_Mask             = 0b0000000011111111
        PartB_RightShift       = 0
        Other_Mask             = 0b1111111111111111
        Other_RightShift       = 0
        PTY_Mask               = 0b1111100000000000
        PTY_RightShift         = 11
        TA_Mask                = 0b0000000000000001
        TA_RightShift          = 0        
        
        VariantCode            = (self.radioRegister[self.RDSB] & VariantCode_Mask) >> VariantCode_RightShift
        PartA                  = (self.radioRegister[self.RDSC] & PartA_Mask) >> PartA_RightShift
        PartB                  = (self.radioRegister[self.RDSC] & PartB_Mask) >> PartB_RightShift
        Other                  = (self.radioRegister[self.RDSC] & Other_Mask) >> Other_RightShift
        PTY                    = (self.radioRegister[self.RDSC] & PTY_Mask) >> PTY_RightShift
        TA                     = (self.radioRegister[self.RDSC] & TA_Mask) >> TA_RightShift

        PinDay_Mask          = 0b1111100000000000
        PinDay_RightShift    = 11
        PinHour_Mask         = 0b0000011111000000
        PinHour_RightShift   = 6
        PinMinute_Mask       = 0b0000000000111111
        PinMinute_RightShift = 0
        
        PinDay    = (self.radioRegister[self.RDSC] & PinDay_Mask) >> PinDay_RightShift
        PinHour   = (self.radioRegister[self.RDSC] & PinHour_Mask) >> PinHour_RightShift
        PinMinute = (self.radioRegister[self.RDSC] & PinMinute_Mask) >> PinMinute_RightShift
        Pin       = ("0"+str(PinDay))[-2:] + ("0"+str(PinHour))[-2:] + ("0"+str(PinMinute))[-2:]

        if (silent == 0):
            if  (0b0000 <= VariantCode <= 0b0011):print ("PS: index;" + str(VariantCode) + "-" + chr(PartA) + chr(PartB))
            elif(VariantCode == 0b0100):print ("Alt. Freq.: " + str((PartA + 875)/10) + " + " + str((PartB + 875)/10))
            elif(0b0101 <= VariantCode <= 0b1001):print ("Tuning freq. : " + str((PartA + 875)/10) + " Mapped FM freq. " + str(VariantCode - 5) + " : " + str((PartB + 875)/10) )
            elif(0b1010 <= VariantCode <= 0b1011):print ("Unallocated: " + str(Other))
            elif(VariantCode == 0b1100):print ("Linkage information: " + str(Other) )
            elif(VariantCode == 0b1101):print ("PTY: " + str(PTY) + " TA: " + str(TA) )
            elif(VariantCode == 0b1110):print ("PIN: " + str(Pin) )
            elif(VariantCode == 0b1111):print ("Reserved for broadcasters use: " + str(Other) )
        
