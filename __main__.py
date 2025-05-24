# Imports

import time
import sys
import select
import logging
from datetime import datetime

# Variables

run = True # Run Main Program Loop

cont = 0 # Value read from file (graphed value/output)

runGraph = True # Should Run Graph Loop (Stops "Run" if it will encounter known bugs)

error = '' # Error str shown on first line of graph when not empty
lastErr = '' # Used to prevent logging repeats

logging.basicConfig( # Logging
    level=logging.ERROR,
    format='%(asctime)s:\n %(message)s\n',
    filename='app.log'
)

# Defaults

values = { # Value Settings, explained in instructions
  
  'path': '/sys/class/thermal/thermal_zone0/temp',
  'scale': 1000,
  'method': 0,
  'methodInfo': ['0'],
  
  'doLog': 0.0,
  'log': 'log.txt',
  'logMax': 100.0,
  'logMin': 0.0,
  'logInc': 0.0,
  
  'spf': 1.0,
  'logLen': 20.0,
  'numLen': 6.0,
  
  'barMin': 20.0,
  'barMax': 100.0,
  'barLen': 50.0,
  'barMed': .7,
  'barHi': .85,
  'barChr': '|',
  'barLoC': 32.0,
  'barMedC': 33.0,
  'barHiC': 31.0
  
}

# Keys
# (Printed Info)

types = { # Path, scale, method, method info, description
  'thermal': ['/sys/class/thermal/thermal_zone0/temp',
              1000,
              0,
              ['0'],
              'Core temp in Celcius'],
  'memfr': ['/proc/meminfo',
              1024,
              0,
              ['1'],
              'Free memory in MB'],
  'netrx': ['/sys/class/net/eth0/statistics/rx_bytes',
             1,
             1,
             ['0', ''],
             'Bytes received. "eth0" can be interchanged for different network device'],
  'nettx': ['/sys/class/net/eth0/statistics/tx_bytes',
             1,
             1,
             ['0', ''],
             'Bytes transmitted. "eth0" can be interchanged for different network device'],
  'cpuload': ['/proc/stat',
             0.01,
             2,
             ['1', '4', '', ''],
             'Total CPU load as %, methodInfo[0] can be changed to change core'],
  'diskr': ['/proc/diskstats',
             2,
             3,
             ['24', '5', ''],
             'KB read on disk (sectors (512 Bytes) * 2 )'],
  'diskw': ['/proc/diskstats',
             2,
             3,
             ['24', '9', ''],
             'KB written on disk (sectors (512 Bytes) * 2 )']
}

colorKey = ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan'] # starts at 31 (red)

# Functions

def strToFloat(string): # Converts string to float, returns 0 if no number, ignores non-numeric characters
  
  numStr = '' # Init refined string
  
  for i in range(len(string)): # Only add numeric and .'s to numStr
    
    if string[i].isnumeric(): numStr = numStr + string[i]
    if string[i] == '.': numStr = numStr + string[i]
    
  
  if len(numStr) == 0: return 0 # if no numerics, return 0
  
  if string[0] == '-': return -1 * float(numStr) # If 1st char is "-", negetive
  else: return float(numStr) # Return (positive)
  

def lenNum(string, length): # Returns number str to str of length 'length'
  
  if strToFloat(string) >= 10 ** length: # Should use scientific notation
    
    num = strToFloat(string)
    pwr = 0
    
    while num >= 10: # Gets pwr
      pwr += 1
      num = num / 10
    
    return str(num)[:3] + 'e' + str(pwr) # Return sci. note.
    
  
  string = string[:length] # Trim to length
  
  add = length - len(string) # Length to add (if string is too short)
  
  out = string
  
  for i in range(add): out = out + '0' # Add needed length (if too short)
  
  return out # Return
  

def bar(val, minimum, maximum, length, medium, high, char, loColor, medColor, hiColor):
  # Creates a bar (str) for the graph
  
  # Validating
  
  val = max(min(val, maximum), minimum)
  
  length = int(max(length, 0)) 
  
  loColor = int(max(min(loColor, 36), 31))
  medColor = int(max(min(medColor, 36), 31))
  hiColor = int(max(min(hiColor, 36), 31))
  
  # Variables
  
  val = val - minimum # Set min to 0 relative to val
  
  span = maximum - minimum # Span between min & max
  
  barLen = round((val / span) * length) # Height of bar (num chars)
  
  # Output
  
  out = str(minimum) +  '[\033[' + str(loColor) + 'm' # Init out
  #     ^ Min value      ^ Bar bracket  ^ Low color esc char
  
  for i in range(barLen):
    
    if i / length >= high: out = out + '\033[' + str(hiColor) + 'm' # High color
    elif i / length >= medium: out = out + '\033[' + str(medColor) + 'm' # Med color
    
    out = out + char # Add char
    
  
  for i in range(length - barLen): out = out + ' ' # Empty space/filler
  
  out = out + '\033[0m]' + str(maximum) # Max at end
  
  return out
  

def printLog(log, new): # Prints log with new entry (rolls graph)
  
  # Roll
  
  log.pop(0)
  
  log.append(new)
  
  # Error
  
  global error
  if error != '': log[0] = error
  
  # Print
  
  for entry in log: print('\033[F', end = '') # Clear
  
  for entry in log: print('\r' + entry, end = '\n') # Print
  
  return log # Return new log
  

def getCont(path, method): # Gets value from file (uses methods)
  
  out = 0
  
  if int(method) == 0: # 
    
    with open(path, 'r') as file: cont = file.readlines() # Read file (as array)
    
    out = strToFloat(cont[int(values['methodInfo'][0])]) # out = strToFloat of file line
    
  
  elif int(method) == 1:
    
    with open(path, 'r') as file: cont = file.readlines() # Read file (as array)
    
    new = strToFloat(cont[int(values['methodInfo'][0])]) # new = strToFloat of file line
    
    out = new - strToFloat(values['methodInfo'][1]) # out = new - old
    out = out / values['spf'] # Divide by seconds per frame (so it is change per second)
    
    values['methodInfo'][1] = str(new) # old = new
    
  
  elif int(method) == 2:
    
    with open(path, 'r') as file: cont = file.readlines() # Read file (as array)
    
    line = cont[int(values['methodInfo'][0])][:-1].split() # Break line into array
    
    newTotal = sum(float(num) for num in line[1:]) # Sum line array
    
    newVal = int(line[int(values['methodInfo'][1])]) # Get newVal from indexing
    
    oldTotal = strToFloat(values['methodInfo'][2]) # Get old total
    oldVal = strToFloat(values['methodInfo'][3]) # Get old val
    
    total = (newTotal - oldTotal) / values['spf'] # Get total rate of change (divided by seconds per frame)
    val = (newVal - oldVal) / values['spf'] # Get val rate of change (divided by seconds per frame)
    
    out = (total - val) / total # Invert val and divide by total (fraction)
    
    values['methodInfo'][2] = str(newTotal) # Set old total
    values['methodInfo'][3] = str(newVal) # Set old val
    
  
  elif int(method) == 3:
    
    with open(path, 'r') as file: cont = file.readlines() # Read file (as array)
    
    line = cont[int(values['methodInfo'][0])][:-1].split() # Break line into array
    
    newVal = int(line[int(values['methodInfo'][1])]) # Get newVal from indexing
    oldVal = strToFloat(values['methodInfo'][2]) # Get old val
    
    val = (newVal - oldVal) / values['spf'] # Divide by seconds per frame (so it is change per second)
    
    out = val
    
    values['methodInfo'][2] = str(newVal) # old = new
    
  
  return out / values['scale'] # Return divided by scale
  
def detectKey(): # Detects key press (used for exiting graph loop)
  
  if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
    key = sys.stdin.read(1) # Read input log
    return key # Return
  
  return None # Base
  

def getTypes():
  
  global types
  
  
  

# Instructions

instructions = [
  'Inputs:',
  '  Case does not matter',
  '  Numbers are validated before use',
  '    (if logLen is set to -5.2 it will be treated as 1)',
  '  If there is an error with getCont(), 0 is returned',
  '  For inputs that set values, input key/name, then you will be prompted to set value',
  '',
  '  "quit": Quits',
  '  "run": Run graph loop (must kill program to stop)',
  '  "spf": Seconds per frame for graph, Default: 1',
  '  "logLen": How many lines are recorded, Default: 20',
  '  "numLen": Length of ending number, Default: 6',
  '  "?": Reprint this',
  '',
  '  "import": Import settings from file (.txt) (Will ask for file name)',
  '  "doLog": Log or not, 1 = True, else False, Default: 0 (False)',
  '  "log": Set path of log file, Default: "log.txt"',
  '  "logMax": Lower value of logging range (inclusive), Default: 90',
  '  "logMin": Upper value of logging range (inclusive), Default: 0',
  '  "logInc": Is inclusive of range (if not, exclusive), 1 = True, else False, Default: 0 (False)',
  '',
  '  "path": File path for data file, Defualt: (for thermal)',
  '  "scale": Scale of return value, Default: 1000',
  '  "method": Method for gathering info, Default: 0',
  '  "methodInfo": Other info needed for gathering data, Default: ["0"]',
  '  "type": Looks up paths saved in list for data file',
  '  "type?": Print types in array noted above',
  '',
  '  "barMin": Default: 20',
  '  "barMax": Default: 100',
  '  "barLen": number of chars in bar, Default: 50',
  '  "barMed": Medium Threshold (0 to 1), Default: 0.7',
  '  "barHi": High Threshold (0 to 1), Default: 0.85',
  '  "barChr": Character used in bar, Default: "|"',
  '  "barLoC": Low color, Default: 32 (green)',
  '  "barMedC": Medium color, Default: 33 (yellow)',
  '  "barHiC": High color, Default: 31 (red)',
  '  "c?": Print color key'
]

for entry in instructions: print(entry) # Print Instructions

# Try Opening Sys File

try:
  with open(values['path'], 'r') as file: pass
except:
  print('\nUnable to Open file :/')
  runGraph = False

# Main Loop

while run:
  
  # Inupt Loop
  
  while True:
    
    print()
    inp = input('Input: ')
    print()
    
    inp = inp.lower() # Set to lower
    
    # Quit and Run
    
    if inp == 'quit':
      run = False
      runGraph = False
      break
    
    elif inp == 'run':
      
      if runGraph: break
      
      print('Error')
      
    
    # import
    
    elif inp == 'import':
      
      valInp = input('Path: ') # Prompt path
      print()
      
      # Try to open
      
      try:
        with open(valInp, 'r') as file: cont = file.readlines() # Read as array
      except:
        print('Unable to Open :/') # Error
      
      else:
        
        for line in cont:
          
          line = line.replace('\n', '') + ':  ' # Format (remove '\n' and add ': ')
          
          pair = line.split(': ') # Split (to array) on ': '
          
          key = pair[0].lower() # Get key
          val = pair[1] # Get val
          
          match = False # Match base case
          
          for vKey in values:
            if vKey.lower() == key: match = True # If key is valid (match)
          
          if match: # If valid
            
            # String
            
            if key == 'log':
              
              try:
                with open(val, 'r') as file: pass
              except:
                print('Unable to Open "' + val + '" :/')
                runGraph = False
              else:
                values['log'] = val
                print('"log" set to "' + values['log'] + '"')
                runGraph = True
              
            
            elif key == 'path':
              
              try:
                with open(val, 'r') as file: pass
              except:
                print('Unable to Open "' + val + '" :/')
                runGraph = False
              else:
                values['path'] = val
                print('"path" set to "' + values['path'] + '"')
                runGraph = True
              
            
            elif key == 'barchr':
              
              values['barChr'] = (val + ' ')[0]
              print('"barChr" set to "' + values['barChr'] + '"')
              
            
            # Array
            
            elif key == "methodinfo":
              
              values['methodInfo'] = val.split()
              print('"methodInfo" set to "' + str(values['methodInfo']) + '"')
              
            
            # All Other
            
            else:
              
              values[key] = strToFloat(val)
              
              print('"' + key +'" set to "' + str(values[key]) + '"')
              
            
          
        
      
    
    # Info
    
    elif inp == '?':
      for entry in instructions: print(entry)
    
    elif inp == 'type?':
      for key in types: print(key + ': ' + types[key][0] +
                              ', scale: ' + str(types[key][1]) +
                              ', method: ' + str(types[key][2]) +
                              ', methodInfo: ' + str(types[key][3]) +
                              '\n  ' + types[key][4])
    
    elif inp == 'c?':
      for i in range(len(colorKey)): print(colorKey[i] + ': ' + str(i+31))
    
    # Type
    
    elif inp == 'type':
      
      valInp = input('"type": ') # Prompt type
      print()
      
      for key in types:
        
        if valInp == key:
          
          # Try to open file
          
          try:
            with open(types[key][0], 'r') as file: pass
          except:
            print('Unable to Open :/')
            runGraph = False # Error
          else:
            values['path'] = types[key][0]
            print('"path" set to "' + values['path'] + '"')
            
            values['scale'] = types[key][1]
            print('"scale" set to "' + str(values['scale']) + '"')
            
            values['method'] = types[key][2]
            print('"method" set to "' + str(values['method']) + '"')
            
            values['methodInfo'] = types[key][3]
            print('"methodInfo" set to "' + str(values['methodInfo']) + '"')
            
            runGraph = True
            
          
        
      
    
    # String Input
    
    elif inp == 'log':
      
      valInp = input('"log": ')
      print()
      
      # Try to open file
      
      try:
        with open(valInp, 'r') as file: pass
      except:
        print('Unable to Open :/')
        runGraph = False # Error
      else:
        values['log'] = valInp
        print('"log" set to "' + values['log'] + '"')
        runGraph = True
      
    
    elif inp == 'path':
      
      valInp = input('"path": ')
      print()
      
      # Try to open file
      
      try:
        with open(valInp, 'r') as file: pass
      except:
        print('Unable to Open :/')
        runGraph = False
      else:
        values['path'] = valInp
        print('"path" set to "' + values['path'] + '"')
        runGraph = True # Error
      
    
    elif inp == 'barchr':
      
      valInp = input('"barChr": ')
      print()
      
      values['barChr'] = (valInp + ' ')[0]
      print('"barChr" set to "' + values['barChr'] + '"')
      
    
    # Method Info / Array Input
    
    elif inp == "methodinfo":
      
      valInp = input('"methodInfo": ')
      print()
      
      values['methodInfo'] = valInp.split()
      print('"methodInfo" set to "' + str(values['methodInfo']) + '"')
      
    
    # All Other (floats)
    
    else:
      
      for key in values:
        
        if inp == key.lower():
          
          valInp = input('"' + key + '": ')
          print()
          
          values[key] = strToFloat(valInp)
          
          print('"' + key +'" set to "' + str(values[key]) + '"')
          
        
      
    
  
  # Pre-Graph
  
  if runGraph:
    
    contLog = [''] * int(max(values['logLen'], 1)) # Clear log
    
    print('Enter "q" to return to Input (wait until loop has ended)') # Instructions
    
    for entry in contLog: print('') # First log print
    
  
  # Graph Loop
  
  while runGraph:
    
    # Key (quit)
    
    if detectKey() == 'q':
      break
    
    # Read sys file
    
    try:
      cont = getCont(values['path'], values['method'])
    except Exception as e:
      if e != lastErr: logging.exception(e)
      lastErr = e
      cont = 0
      error = 'Error Getting Content' # Error
    
    # Log
    
    shouldLog = False
    
    if values['logInc'] == 1.0: # Log inclusive range
      if cont >= values['logMin'] and cont <= values['logMax']: shouldLog = True
    else: # Log exlusive range
      if cont <= values['logMin']: shouldLog = True
      if cont >= values['logMax']: shouldLog = True
    
    if shouldLog and values['doLog'] == 1.0: # Should log
      
      # Try to write to file
      
      try:
        with open(values['log'], 'a') as file:
          t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          file.write(str(t) + ' in "' + values['path'] + '": ' + str(cont) + '\n')
      except Exception as e:
        if e != lastErr: logging.exception(e)
        lastErr = e
        error = 'Error Writing to Log' # Error
      
    
    # Print
    
    newLog = bar(cont,
                 values['barMin'],
                 values['barMax'],
                 values['barLen'],
                 values['barMed'],
                 values['barHi'],
                 values['barChr'],
                 values['barLoC'],
                 values['barMedC'],
                 values['barHiC']) # Bar
    
    newLog = (newLog + ' | ' +
              lenNum(str(cont), int(max(values['numLen'], 0))) +
              '  ') # Add number to end
    
    contLog = printLog(contLog, newLog) # Roll
    
    # Time
    
    time.sleep(max(values['spf'], 0))
    
  
