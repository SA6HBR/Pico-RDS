# Pico-RDS
Connect a raspberry pi pico to radio-chip si4703 RDS

![alt text](https://github.com/SA6HBR/Pico-RDS/blob/main/image/circuit.png "Interface")  
  
Install and run pythoncode with Thonny.

Menu:
```
pu - Power up
pd - Power down
2  - Seek up
1  - Seek down
+  - Volume up
-  - Volume down
4A - Get time from RDS
```
Power up si4703 with write pu and press enter.

Some RDS info:
```
TP         : 1
PTY        : 4
PI Country : Sweden
PI Type    : Regional: 11
PI Referens: SR P4
```
```
GroupType  : 0A
3.1.5.1 Type 0 groups: Basic tuning and switching information
DI : 1, MS : 0, TA : TA & EON, Index : 3 [ : ]
ProgrammeService : P4 SR   
Alt. freq. A: 103.8
Alt. freq. B: 102.9 
```
```
GroupType  : 1A
3.1.5.2 Type 1 groups: Programme Item Number and slow labelling codes
Programme item number code : 261503 Radio Paging Codes: 0 LinkageActuator: 0 VariantCode: 7
Identification of EWS channel: 10
```
```
GroupType  : 2A
3.1.5.3 Type 2 groups: RadioText
 T_flag: 0, RT_index: 2 ra
RadioTextA : Sportextra                                                      
RadioTextB :    
```
```
GroupType  : 14A
3.1.5.19 Type 14 groups: Enhanced Other Networks information
Other Networks TP:0, PiCountry: e, PiType: 2, PiReferens: 0
Tuning freq. : 103.8 Mapped FM freq. 0 : 98.8
```

  
  
## Useful Links

* [Circuit](https://github.com/SA6HBR/Pico-RDS/blob/main/CircuitDiagram/raspberryPiPicoRDS.pdf)
* [AN230 Programming guide](https://github.com/SA6HBR/Pico-RDS/blob/main/pdf/AN230_PROGRAMMING_GUIDE.pdf)
* [Si4703 data sheet](https://github.com/SA6HBR/Pico-RDS/blob/main/pdf/Si4702-03-C19-1.pdf)
* [EN50067 RDS Standard](https://github.com/SA6HBR/Pico-RDS/blob/main/pdf/EN50067_RDS_Standard.pdf)
* [KiCad](https://www.kicad.org/)
* [Thonny](https://thonny.org/)



## License

GNU General Public License v3.0, see [LICENSE](https://github.com/SA6HBR/Pico-RDS/blob/main/LICENSE) for details.
