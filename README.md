# Basics

This is python script that reads `/sys` and `/proc` (or similar). It is made for Raspberry Pi OS, but should work similarly on other Linux OS's. It takes the values from the files and graphs them overtime. There are different graph and system variables that can be edited, it is explained when ran. These variables are stored in the `values` dictionary for easy access.

[Somewhat usefull Linux documentation](https://www.kernel.org/doc/Documentation/ABI/testing/)

## Screenshot (Raspi, Rasberry Pi Linux, through SSH on Chrome)

![Screenshot 2025-04-22 9 15 01 AM](https://github.com/user-attachments/assets/b6599e9c-8f60-4995-830e-f8bc46cb009d)

# File Structures

## __main__.py

<pre style="overflow-x: scroll;">
  Import
  
  Vars
  
  Functions
  
  Pre-Loop (File and Printing Stuff)
  
  Main Loop {
    
    Input Loop {
      
      Many elifs in series
      
      Else/Base case (floats in 'values' dictionary)
      
      Break to exit
      
    }
    
    Pre-Graphing
    
    Graphing Loop {
      
      Break to exit
      
      Get Value
      
      Log Logic
      
      Print/Render
      
      Timing/FPS
      
    }
    
  }
</pre>

## Settings ("settings.txt" by default)

Formated like how you change the values in the program, with ": " seperating key and value. And each line being a new key-value pair.

<pre style="overflow-x: scroll;">
  [Key]: [Val]
</pre>

EX:

<pre style="overflow-x: scroll;">
  barChr: |
  bArmIn: 0.9haksd [Taken as "barMin: 0.9"]
</pre>

## Log ("log.txt" by default)

<pre style="overflow-x: scroll;">
  YYYY-MM-DD HH:MM:SS in "Path": ###
</pre>

EX:

<pre style="overflow-x: scroll;">
   2025-03-25 3:34:51 in "/sys/class/thermal/thermal_zone0/temp": 95.32
   2025-03-25 18:35:06 in "/sys/class/thermal/thermal_zone0/temp": -1.0
</pre>

# Printed Documentation

## General (Printed on Start)

<pre style="overflow-x: scroll;">
Inputs:
  Case does not matter
  Numbers are validated before use
    (if logLen is set to -5.2 it will be treated as 1)
  If there is an error with getCont(), 0 is returned
  For inputs that set values, input key/name, then you will be prompted to set value

  "quit": Quits
  "run": Run graph loop (must kill program to stop)
  "spf": Seconds per frame for graph, Default: 1
  "logLen": How many lines are recorded, Default: 20
  "numLen": Length of ending number, Default: 6
  "?": Reprint this

  "import": Import settings from file (.txt) (Will ask for file name)
  "doLog": Log or not, 1 = True, else False, Default: 0 (False)
  "log": Set path of log file, Default: "log.txt"
  "logMax": Lower value of logging range (inclusive), Default: 90
  "logMin": Upper value of logging range (inclusive), Default: 0
  "logInc": Is inclusive of range (if not, exclusive), 1 = True, else False, Default: 0 (False)

  "path": File path for data file, Defualt: (for thermal)
  "scale": Scale of return value, Default: 1000
  "method": Method for gathering info, Default: 0
  "methodInfo": Other info needed for gathering data, Default: ["0"]
  "type": Looks up paths saved in list for data file
  "type?": Print types in array noted above

  "barMin": Default: 20 
  "barMax": Default: 100
  "barLen": number of chars in bar, Default: 50
  "barMed": Medium Threshold (0 to 1), Default: 0.7
  "barHi": High Threshold (0 to 1), Default: 0.85
  "barChr": Character used in bar, Default: "="
  "barLoC": Low color, Default: 32 (green)
  "barMedC": Medium color, Default: 33 (yellow)
  "barHiC": High color, Default: 31 (red)
  "c?": Print color key
</pre>

## Color Key

<pre style="overflow-x: scroll;">
red: 31
green: 32
yellow: 33
blue: 34
magenta: 35
cyan: 36
</pre>

[Useful resource for terminal styling](https://stackoverflow.com/questions/4842424/list-of-ansi-color-escape-sequences)

## Types Array

<pre style="overflow-x: scroll;">
thermal: /sys/class/thermal/thermal_zone0/temp, scale: 1000, method: 0, methodInfo: ['0']
  Core temp in Celcius
memfr: /proc/meminfo, scale: 1024, method: 0, methodInfo: ['1']
  Free memory in MB
netrx: /sys/class/net/eth0/statistics/rx_bytes, scale: 1, method: 1, methodInfo: ['0', '']
  Bytes received. "eth0" can be interchanged for different network device
nettx: /sys/class/net/eth0/statistics/tx_bytes, scale: 1, method: 1, methodInfo: ['0', '']
  Bytes transmitted. "eth0" can be interchanged for different network device
cpuload: /proc/stat, scale: 0.01, method: 2, methodInfo: ['1', '4', '', '']
  Total CPU load as %, methodInfo[0] can be changed to change core
diskr: /proc/diskstats, scale: 2, method: 3, methodInfo: ['24', '5', '']
  KB read on disk (sectors (512 Bytes) * 2 )
diskw: /proc/diskstats, scale: 2, method: 3, methodInfo: ['24', '9', '']
  KB written on disk (sectors (512 Bytes) * 2 )
</pre>

# Method

`values['method']` and `values['methodInfo']` tells the script how to read files. `values['method']` is a float passed into a function, changed to an interger, and then compared with many elif's. This causes different behaviors. `values['methodInfo']` is a list of strings that stores data needed for handling each method.

## Each Method:

| Method | Description | Equation | methodInfo | For |
| ------ | ----------- | -------- | ---------- | --- |
| 0 | Raw: Reads one line, converts string to float | N/A | [line] | Thermal, Memory |
| 1 | Reads a single line of a cumulated value, and finds rate of change | out = (new - old) / `values['spf']` | [line, old] | Network |
| 2 | Reads a line and breaks it into a list, sums the list for total and takes a position for another value | total = ((newTotal - oldTotal) / `values['spf']`), val = ((newVal - oldVal) / `values['spf']`), out = (total - val) / total | [line, valPos, oldTotal, oldVal] | CPU Load |
| 3 | Similar to method 2 in structure, although only outputs a single value similar to method 1 | out = (new - old) / `values['spf']` | [line, valPos, oldVal] | Disk
