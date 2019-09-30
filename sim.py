from __future__ import print_function
import os

# Function List:
# 1. netRead: read the benchmark file and build circuit netlist
# 2. gateCalc: function that will work on the logic of each gate
# 3. inputRead: function that will update the circuit dictionary made in netRead to hold the line values
# 4. basic_sim: the actual simulation
# 5. main: The main function

# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Neatly prints the Circuit Dictionary:
def printCkt (circuit):
    print("INPUT LIST:")
    for x in circuit["INPUTS"][1]:
        print(x + "= ", end='')
        print(circuit[x])

    print("\nOUTPUT LIST:")
    for x in circuit["OUTPUTS"][1]:
        print(x + "= ", end='')
        print(circuit[x])

    print("\nGATE list:")
    for x in circuit["GATES"][1]:
        print(x + "= ", end='')
        print(circuit[x])
    print()


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Reading in the Circuit gate-level netlist file:
def netRead(netName):
    # Opening the netlist file:
    netFile = open(netName, "r")
    outputFile = open('full_f_list', "w")

    # temporary variables
    inputs = []     # array of the input wires
    outputs = []    # array of the output wires
    gates = []      # array of the gate list
    inputBits = 0   # the number of inputs needed in this given circuit
    total_faults = 0 # the number of faults per inputs, outputs, and gate inputs/outputs
    full_fault_list = [] # array of the full fault list


    # main variable to hold the circuit netlist, this is a dictionary in Python, where:
    # key = wire name; value = a list of attributes of the wire
    circuit = {}

    # Reading in the netlist file line by line
    for line in netFile:

        # NOT Reading any empty lines
        if (line == "\n"):
            continue

        # Removing spaces and newlines
        line = line.replace(" ","")
        line = line.replace("\n","")

        # NOT Reading any comments
        if (line[0] == "#"):
            continue

        # @ Here it should just be in one of these formats:
        # INPUT(x)
        # OUTPUT(y)
        # z=LOGIC(a,b,c,...)

        # Read a INPUT wire and add to circuit:
        if (line[0:5] == "INPUT"):
            # wire SA-0 and SA-1
            total_faults += 2
            # Removing everything but the line variable name
            line = line.replace("INPUT", "")
            line = line.replace("(", "")
            line = line.replace(")", "")

            # Format the variable name to wire_*VAR_NAME*
            # Wire_names --> preserve the wire names
            wire_names = line
            line = "wire_" + line

            # Stuck at 0 and at 1 line formatting
            sa_0 = wire_names + "-SA-0"
            sa_1 = wire_names + "-SA-1"

            # Append the input wire stuck at faults to the full fault list
            full_fault_list.append(sa_0)
            full_fault_list.append(sa_1)

            # Error detection: line being made already exists
            if line in circuit:
                msg = "NETLIST ERROR: INPUT LINE \"" + line + "\" ALREADY EXISTS PREVIOUSLY IN NETLIST"
                print(msg + "\n")
                return msg

            # Appending to the inputs array and update the inputBits
            inputs.append(line)

            # add this wire as an entry to the circuit dictionary
            circuit[line] = ["INPUT", line, False, 'U']

            inputBits += 1
            print(line)
            print(circuit[line])
            print(sa_0)
            print(sa_1)
            print("")
            continue

        # Read an OUTPUT wire and add to the output array list
        # Note that the same wire should also appear somewhere else as a GATE output
        if line[0:6] == "OUTPUT":
            # Removing everything but the numbers
            line = line.replace("OUTPUT", "")
            line = line.replace("(", "")
            line = line.replace(")", "")

            # Appending to the output array
            outputs.append("wire_" + line)
            continue

        # Read a gate output wire, and add to the circuit dictionary
        lineSpliced = line.split("=") # splicing the line at the equals sign to get the gate output wire
        # preserve output wire name
        outputWire = lineSpliced[0]
        gateOut = "wire_" + lineSpliced[0]

        # Count the number of gate output wires
        total_faults += 2

        # Error detection: line being made already exists
        if gateOut in circuit:
            msg = "NETLIST ERROR: GATE OUTPUT LINE \"" + gateOut + "\" ALREADY EXISTS PREVIOUSLY IN NETLIST"
            print(msg+"\n")
            return msg

        # Appending the dest name to the gate list
        gates.append(gateOut)

        lineSpliced = lineSpliced[1].split("(") # splicing the line again at the "("  to get the gate logic
        logic = lineSpliced[0].upper()


        lineSpliced[1] = lineSpliced[1].replace(")", "")
        terms = lineSpliced[1].split(",")  # Splicing the the line again at each comma to the get the gate terminals
        # Turning each term into an integer before putting it into the circuit dictionary
        # wire_names --> preserve the wire names
        wire_names = terms
        terms = ["wire_" + x for x in terms]

        # add the gate output wire to the circuit dictionary with the dest as the key
        circuit[gateOut] = [logic, terms, False, 'U']
        print(gateOut)
        print(circuit[gateOut])        

        print("WIRE NAMES")
        print(wire_names)  
        print(outputWire  + "-SA-0")
        print(outputWire  + "-SA-1")       
        
        # Append the gate output wire stuck at faults to the full fault list
        full_fault_list.append(outputWire  + "-SA-0")
        full_fault_list.append(outputWire  + "-SA-1")   
        
        for x in wire_names:
            total_faults += 2

            # stuck at 0 and at 1 line formatting
            sa_0 = outputWire + "-IN-" + x + "-SA-0"
            sa_1 = outputWire + "-IN-" + x + "-SA-1"
            print(sa_0)
            print(sa_1)

            # Append the gate input wires stuck at faults to the full fault list
            full_fault_list.append(sa_0)
            full_fault_list.append(sa_1)
        
        print("")

    # now after each wire is built into the circuit dictionary,
    # add a few more non-wire items: input width, input array, output array, gate list
    # for convenience
    
    circuit["INPUT_WIDTH"] = ["input width:", inputBits]
    circuit["INPUTS"] = ["Input list", inputs]
    circuit["OUTPUTS"] = ["Output list", outputs]
    circuit["GATES"] = ["Gate list", gates]

    print("\n bookkeeping items in circuit: \n")
    print('TOTAL FAULTS: ')
    print(total_faults)
    print(circuit["INPUT_WIDTH"])
    print(circuit["INPUTS"])
    print(circuit["OUTPUTS"])
    print(circuit["GATES"])

    outputFile.write('# circuit.bench\n# full SSA fault list\n\n')
    for line in full_fault_list:
        outputFile.write(line + '\n')
    outputFile.write('\n# total faults: ' + str(total_faults))

    return circuit


# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: calculates the output value for each logic gate
def gateCalc(circuit, node):

    # terminal will contain all the input wires of this logic gate (node)
    terminals = list(circuit[node][1])  
    # print("THIS IS THE FUCKING NODES")
    # print(node)
    # print(circuit[node])
    # print(circuit[node][0])

    # print ("THIS IS THE FUCKIING TERMINALS")
    # print(terminals[0])
    # print(circuit[terminals[0]])
    # print("")

    # If the node is an Inverter gate output, solve and return the output
    if circuit[node][0] == "NOT":
        if circuit[terminals[0]][3] == '0':
            circuit[node][3] = '1'
        elif circuit[terminals[0]][3] == '1':
            circuit[node][3] = '0'
        elif circuit[terminals[0]][3] == "U":
            circuit[node][3] = "U"
        else:  # Should not be able to come here
            return -1
        return circuit

    # If the node is an AND gate output, solve and return the output
    elif circuit[node][0] == "AND":
        # Initialize the output to 1
        circuit[node][3] = '1'
        # Initialize also a flag that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 0 at any input terminal, AND output is 0. If there is an unknown terminal, mark the flag
        # Otherwise, keep it at 1
        for term in terminals:  
            if circuit[term][3] == '0':
                circuit[node][3] = '0'
                break
            if circuit[term][3] == "U":
                unknownTerm = True

        if unknownTerm:
            if circuit[node][3] == '1':
                circuit[node][3] = "U"
        return circuit

    # If the node is a NAND gate output, solve and return the output
    elif circuit[node][0] == "NAND":
        # Initialize the output to 0
        circuit[node][3] = '0'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 0 terminal, NAND changes the output to 1. If there is an unknown terminal, it
        # changes to "U" Otherwise, keep it at 0
        for term in terminals:
            if circuit[term][3] == '0':
                circuit[node][3] = '1'
                break
            if circuit[term][3] == "U":
                unknownTerm = True
                break

        if unknownTerm:
            if circuit[node][3] == '0':
                circuit[node][3] = "U"
        return circuit

    # If the node is an OR gate output, solve and return the output
    elif circuit[node][0] == "OR":
        # Initialize the output to 0
        circuit[node][3] = '0'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 1 terminal, OR changes the output to 1. Otherwise, keep it at 0
        for term in terminals:
            if circuit[term][3] == '1':
                circuit[node][3] = '1'
                break
            if circuit[term][3] == "U":
                unknownTerm = True

        if unknownTerm:
            if circuit[node][3] == '0':
                circuit[node][3] = "U"
        return circuit

    # If the node is an NOR gate output, solve and return the output
    if circuit[node][0] == "NOR":
        # Initialize the output to 1
        circuit[node][3] = '1'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 1 terminal, NOR changes the output to 0. Otherwise, keep it at 1
        for term in terminals:
            if circuit[term][3] == '1':
                circuit[node][3] = '0'
                break
            if circuit[term][3] == "U":
                unknownTerm = True
        if unknownTerm:
            if circuit[node][3] == '1':
                circuit[node][3] = "U"
        return circuit

    # If the node is an XOR gate output, solve and return the output
    if circuit[node][0] == "XOR":
        # Initialize a variable to zero, to count how many 1's in the terms
        count = 0

        # if there are an odd number of terminals, XOR outputs 1. Otherwise, it should output 0
        for term in terminals:
            if circuit[term][3] == '1':
                count += 1  # For each 1 bit, add one count
            if circuit[term][3] == "U":
                circuit[node][3] = "U"
                return circuit

        # check how many 1's we counted
        if count % 2 == 1:  # if more than one 1, we know it's going to be 0.
            circuit[node][3] = '1'
        else:  # Otherwise, the output is equal to how many 1's there are
            circuit[node][3] = '0'
        return circuit

    # If the node is an XNOR gate output, solve and return the output
    elif circuit[node][0] == "XNOR":
        # Initialize a variable to zero, to count how many 1's in the terms
        count = 0

        # if there is a single 1 terminal, XNOR outputs 0. Otherwise, it outputs 1
        for term in terminals:
            if circuit[term][3] == '1':
                count += 1  # For each 1 bit, add one count
            if circuit[term][3] == "U":
                circuit[node][3] = "U"
                return circuit

        # check how many 1's we counted
        if count % 2 == 1:  # if more than one 1, we know it's going to be 0.
            circuit[node][3] = '1'
        else:  # Otherwise, the output is equal to how many 1's there are
            circuit[node][3] = '0'
        return circuit

    # Error detection... should not be able to get at this point
    return circuit[node][0]

# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: calculates the output value for each logic gate using faulty input/outputwires
def faultGateCalc(circuit, node, lineSpliced):
    # terminal will contain all the input wires of this logic gate (node)
    terminals = list(circuit[node][1])  
    accessed = False

    print ("THE FAULT IN CONSIDERATION")
    print (lineSpliced)
    
    # get fault node, terminal, and value
    if (lineSpliced[1] == 'IN'):
        fault_wire_node = 'wire_' + lineSpliced[0]
        fault_wire_term = 'wire_' + lineSpliced[2]
        fault_wire_val = lineSpliced[4]
        # print (fault_wire_node)
        # print (fault_wire_term)
        # print (fault_wire_val)
    else:
        fault_wire_term = 'wire_' + lineSpliced[0]
        fault_wire_node = fault_wire_term
        fault_wire_val = lineSpliced[2]
        # print (fault_wire_node)
        # print (fault_wire_term)
        # print ('NEW VALUE')
        # print (fault_wire_val)
        # print("")

    # print("THIS IS THE CURRENT NODE")
    # print(node)
    # print(lineSpliced[1])
    # print(terminals)

    # print("THIS IS THE CURRENT TERM")
    # print(fault_wire_term)
    # print("OLD VALUE ")
    old_val = circuit[fault_wire_term][3]
    # print(old_val)

    # Change gate input terminal wire value to stuck-at value 
    if node == fault_wire_node and lineSpliced[1] == 'IN':
        for term in terminals:
            if (term == fault_wire_term):
                circuit[term][3] = fault_wire_val
                accessed = True
                # print(term + " is ")
                # print(circuit[term][3])  
    # Change wire value to stuck-at value
    elif lineSpliced[1] != 'IN':
        for term in terminals:
            if (term == fault_wire_term):
                accessed = True                
                circuit[fault_wire_term][3] = fault_wire_val
                # print(fault_wire_term + " now has ")
                # print(circuit[fault_wire_term][3])
    
    # If the node is an Inverter gate output, solve and return the output
    if circuit[node][0] == "NOT":
        if circuit[terminals[0]][3] == '0':
            circuit[node][3] = '1'
        elif circuit[terminals[0]][3] == '1':
            circuit[node][3] = '0'
        elif circuit[terminals[0]][3] == "U":
            circuit[node][3] = "U"
        else:  # Should not be able to come here
            return -1
        if accessed:
            # restore to original value before stuck-at so that it will disrupt other processes that use same wire
            circuit[fault_wire_term][3] = old_val 
        return circuit

    # If the node is an AND gate output, solve and return the output
    elif circuit[node][0] == "AND":
        # Initialize the output to 1
        circuit[node][3] = '1'
        # Initialize also a flag that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 0 at any input terminal, AND output is 0. If there is an unknown terminal, mark the flag
        # Otherwise, keep it at 1
        for term in terminals:  
            if circuit[term][3] == '0':
                circuit[node][3] = '0'
                break
            if circuit[term][3] == "U":
                unknownTerm = True

        if unknownTerm:
            if circuit[node][3] == '1':
                circuit[node][3] = "U"
        if accessed:
            # restore to original value before stuck-at so that it will disrupt other processes that use same wire
            circuit[fault_wire_term][3] = old_val 
        return circuit

    # If the node is a NAND gate output, solve and return the output
    elif circuit[node][0] == "NAND":
        # Initialize the output to 0
        circuit[node][3] = '0'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 0 terminal, NAND changes the output to 1. If there is an unknown terminal, it
        # changes to "U" Otherwise, keep it at 0
        for term in terminals:
            if circuit[term][3] == '0':
                circuit[node][3] = '1'
                break
            if circuit[term][3] == "U":
                unknownTerm = True
                break

        if unknownTerm:
            if circuit[node][3] == '0':
                circuit[node][3] = "U"
        if accessed:
            # restore to original value before stuck-at so that it will disrupt other processes that use same wire
            circuit[fault_wire_term][3] = old_val 
        return circuit

    # If the node is an OR gate output, solve and return the output
    elif circuit[node][0] == "OR":
        # Initialize the output to 0
        circuit[node][3] = '0'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 1 terminal, OR changes the output to 1. Otherwise, keep it at 0
        for term in terminals:
            if circuit[term][3] == '1':
                circuit[node][3] = '1'
                break
            if circuit[term][3] == "U":
                unknownTerm = True

        if unknownTerm:
            if circuit[node][3] == '0':
                circuit[node][3] = "U"
        if accessed:
            # restore to original value before stuck-at so that it will disrupt other processes that use same wire
            circuit[fault_wire_term][3] = old_val 
        return circuit

    # If the node is an NOR gate output, solve and return the output
    if circuit[node][0] == "NOR":
        # Initialize the output to 1
        circuit[node][3] = '1'
        # Initialize also a variable that detects a U to false
        unknownTerm = False  # This will become True if at least one unknown terminal is found

        # if there is a 1 terminal, NOR changes the output to 0. Otherwise, keep it at 1
        for term in terminals:
            if circuit[term][3] == '1':
                circuit[node][3] = '0'
                break
            if circuit[term][3] == "U":
                unknownTerm = True
        if unknownTerm:
            if circuit[node][3] == '1':
                circuit[node][3] = "U"
        if accessed:
            # restore to original value before stuck-at so that it will disrupt other processes that use same wire
            circuit[fault_wire_term][3] = old_val 
        return circuit

    # If the node is an XOR gate output, solve and return the output
    if circuit[node][0] == "XOR":
        # Initialize a variable to zero, to count how many 1's in the terms
        count = 0

        # if there are an odd number of terminals, XOR outputs 1. Otherwise, it should output 0
        for term in terminals:
            if circuit[term][3] == '1':
                count += 1  # For each 1 bit, add one count
            if circuit[term][3] == "U":
                circuit[node][3] = "U"
                if accessed:
                    # restore to original value before stuck-at so that it will disrupt other processes that use same wire
                    circuit[fault_wire_term][3] = old_val 
                return circuit

        # check how many 1's we counted
        if count % 2 == 1:  # if more than one 1, we know it's going to be 0.
            circuit[node][3] = '1'
        else:  # Otherwise, the output is equal to how many 1's there are
            circuit[node][3] = '0'
        if accessed:
            # restore to original value before stuck-at so that it will disrupt other processes that use same wire
            circuit[fault_wire_term][3] = old_val 
        return circuit

    # If the node is an XNOR gate output, solve and return the output
    elif circuit[node][0] == "XNOR":
        # Initialize a variable to zero, to count how many 1's in the terms
        count = 0

        # if there is a single 1 terminal, XNOR outputs 0. Otherwise, it outputs 1
        for term in terminals:
            if circuit[term][3] == '1':
                count += 1  # For each 1 bit, add one count
            if circuit[term][3] == "U":
                circuit[node][3] = "U"
                if accessed:
                    # restore to original value before stuck-at so that it will disrupt other processes that use same wire
                    circuit[fault_wire_term][3] = old_val 
                return circuit

        # check how many 1's we counted
        if count % 2 == 1:  # if more than one 1, we know it's going to be 0.
            circuit[node][3] = '1'
        else:  # Otherwise, the output is equal to how many 1's there are
            circuit[node][3] = '0'
        if accessed:
            # restore to original value before stuck-at so that it will disrupt other processes that use same wire
            circuit[fault_wire_term][3] = old_val 
        return circuit

    # Error detection... should not be able to get at this point
    return circuit[node][0]

# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Updating the circuit dictionary with the input line, and also resetting the gates and output lines
def inputRead(circuit, line):
    # Checking if input bits are enough for the circuit
    if len(line) < circuit["INPUT_WIDTH"][1]:
        return -1

    # Getting the proper number of bits:
    line = line[(len(line) - circuit["INPUT_WIDTH"][1]):(len(line))]

    # Adding the inputs to the dictionary
    # Since the for loop will start at the most significant bit, we start at input width N
    i = circuit["INPUT_WIDTH"][1] - 1
    inputs = list(circuit["INPUTS"][1])
    # dictionary item: [(bool) If accessed, (int) the value of each line, (int) layer number, (str) origin of U value]
    for bitVal in line:
        bitVal = bitVal.upper() # in the case user input lower-case u
        circuit[inputs[i]][3] = bitVal # put the bit value as the line value
        circuit[inputs[i]][2] = True  # and make it so that this line is accessed

        # In case the input has an invalid character (i.e. not "0", "1" or "U"), return an error flag
        if bitVal != "0" and bitVal != "1" and bitVal != "U":
            return -2
        i -= 1 # continuing the increments

    return circuit

# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: the actual simulation #
def basic_sim(circuit, lineSpliced, mode):
    # QUEUE and DEQUEUE
    # Creating a queue, using a list, containing all of the gates in the circuit
    queue = list(circuit["GATES"][1])
    i = 1

    while True:
        i -= 1
        # If there's no more things in queue, done
        if len(queue) == 0:
            break

        # Remove the first element of the queue and assign it to a variable for us to use
        curr = queue[0]
        queue.remove(curr)

        # initialize a flag, used to check if every terminal has been accessed
        term_has_value = True

        # Check if the terminals have been accessed
        for term in circuit[curr][1]:
            if not circuit[term][2]:
                term_has_value = False
                break

        if term_has_value:
            circuit[curr][2] = True
            if mode == 1:
                circuit = gateCalc(circuit, curr)
            else:
                circuit = faultGateCalc(circuit, curr, lineSpliced)


            # ERROR Detection if LOGIC does not exist
            if isinstance(circuit, str):
                print(circuit)
                return circuit

            print("Progress: updating " + curr + " = " + circuit[curr][3] + " as the output of " + circuit[curr][0] + " for:")
            for term in circuit[curr][1]:
                print(term + " = " + circuit[term][3])
            # print("\nPress Enter to Continue...")
            # input()

        else:
            # If the terminals have not been accessed yet, append the current node at the end of the queue
            queue.append(curr)

    return circuit

# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: detects faults for each test vector  
def fault_sim(bench, input, f_list, jedi, sith):
    outputName = 'fault_sim_result'
    outputFailed = open(outputName, "w")
    rank = 1
    # detected_fails = 0
    size = len(sith)
    faults = []

    comment = '# fault sim result\n# input: ' + bench + '\n# input: ' + input + '\n# input: ' + f_list
    outputFailed.write(comment + '\n')

    # padawan = test vector, master = result
    for padawan, master in jedi.items():
        outputFailed.write("\ntv" + str(rank) + " = " + padawan + " -> " + master + " (good)\ndetected:\n")

        # darth = fault in consideration, acolyte = dictionary of faulty outputs
        for darth, acolyte in sith.items(): 
            # hatred = test vector, anger = result
            for hatred, anger in acolyte.items():
                if padawan == hatred:
                    if master != anger:
                        outputFailed.write(darth + ": " + hatred + " -> " + anger + "\n")
                        # detected_fails += 1
                        if darth not in faults:
                            faults.append(darth)
                    continue

        rank += 1
    
    detected_fails = len(faults)
    print (faults)
    
    outputFailed.write("total detected faults: " + str(detected_fails) + "\n\n")
    outputFailed.write("undetected faults: " + str(size - detected_fails) + "\n")

    # Get the undetected faults
    faults = list(set(list(sith.keys())) - set(faults))

    for x in faults:
        outputFailed.write(x + "\n")
    
    outputFailed.write("\nfault coverage: " + str(detected_fails) + "/" + str(size) + " = " + str((detected_fails/size) * 100) + "%")
    outputFailed.close()
    return

# -------------------------------------------------------------------------------------------------------------------- #
# FUNCTION: Main Function
def main():
    # **************************************************************************************************************** #
    # NOTE: UI code; Does not contain anything about the actual simulation

    # Used for file access
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in

    print("Circuit Simulator:")

    # Select circuit benchmark file, default is circuit.bench
    while True:
        cktFile = "circuit.bench"   
        print("\n Read circuit benchmark file: use " + cktFile + "?" + " Enter to accept or type filename: ")
        userInput = input()
        bench = userInput
        if userInput == "":
            break
        else:
            cktFile = os.path.join(script_dir, userInput)
            if not os.path.isfile(cktFile):
                print("File does not exist. \n")
            else:
                break

    print("\n Reading " + cktFile + " ... \n")
    circuit = netRead(cktFile)
    print("\n Finished processing benchmark file and built netlist dictionary: \n")
    # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
    # printCkt(circuit)
    print(circuit)

    # keep an initial (unassigned any value) copy of the circuit for an easy reset
    newCircuit = circuit

    # Select input file, default is input.txt
    while True:
        inputName = "input.txt"
        print("\n Read input vector file: use " + inputName + "?" + " Enter to accept or type filename: ")
        userInput = input()
        preserver = userInput
        if userInput == "":

            break
        else:
            inputName = os.path.join(script_dir, userInput)
            if not os.path.isfile(inputName):
                print("File does not exist. \n")
            else:
                break

    # Select output file, default is output.txt
    while True:
        outputName = "output.txt"
        print("\n Write output file: use " + outputName + "?" + " Enter to accept or type filename: ")
        userInput = input()
        if userInput == "":
            break
        else:
            outputName = os.path.join(script_dir, userInput)
            break

    # Note: UI code;
    # **************************************************************************************************************** #

    print("\n *** Simulating the" + inputName + " file and will output in" + outputName + "*** \n")
    inputFile = open(inputName, "r")
    outputFile = open(outputName, "w")
    good_output = {}
    detect_map = {}

    # Runs the simulator for each line of the input file
    for line in inputFile:
        # Initializing output variable each input line
        output = ""

        # Do nothing else if empty lines, ...
        if (line == "\n"):
            continue
        # ... or any comments
        if (line[0] == "#"):
            continue

        # Removing the the newlines at the end and then output it to the txt file
        line = line.replace("\n", "")
        outputFile.write(line)

        # Removing spaces
        line = line.replace(" ", "")
        
        print("\n before processing circuit dictionary...")
        # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
        # printCkt(circuit)
        print(circuit)
        print("\n ---> Now ready to simulate INPUT = " + line)
        circuit = inputRead(circuit, line)
        # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
        # printCkt(circuit)
        print(circuit)


        if circuit == -1:
            print("INPUT ERROR: INSUFFICIENT BITS")
            outputFile.write(" -> INPUT ERROR: INSUFFICIENT BITS" + "\n")
            # After each input line is finished, reset the netList
            circuit = newCircuit
            print("...move on to next input\n")
            continue
        elif circuit == -2:
            print("INPUT ERROR: INVALID INPUT VALUE/S")
            outputFile.write(" -> INPUT ERROR: INVALID INPUT VALUE/S" + "\n")
            # After each input line is finished, reset the netList
            circuit = newCircuit
            print("...move on to next input\n")
            continue

        circuit = basic_sim(circuit, 'NULL', 1)
        print("\n *** Finished simulation - resulting circuit: \n")
        # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
        # printCkt(circuit)
        print(circuit)     

        for y in circuit["OUTPUTS"][1]:
            if not circuit[y][2]:
                output = "NETLIST ERROR: OUTPUT LINE \"" + y + "\" NOT ACCESSED"
                break
            output = str(circuit[y][3]) + output

        print("\n *** Summary of simulation: ")
        print(line + " -> " + output + " written into output file. \n")
        outputFile.write(" -> " + output + "\n")
        good_output[line] = output

        # After each input line is finished, reset the circuit
        print("\n *** Now resetting circuit back to unknowns... \n")
    
        for key in circuit:
            if (key[0:5]=="wire_"):
                circuit[key][2] = False
                circuit[key][3] = 'U'

        print("\n circuit after resetting: \n")
        # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
        # printCkt(circuit)
        print(circuit)

        print("\n*******************\n")

    print ("*************NOW RUNNING FAULT SIMULATION*************")
    outputFile.close
    inputFile.close
    inputFault = 'f_list.txt'
    outputFault = 'full_fault_sim_result'
    inputFaultFile = open(inputFault, "r")
    outputFaultFile = open(outputFault, "w")
    curr_bad_output = {}

    # Reading in the fault_list1 file line by line
    for fault in inputFaultFile:
        
        inputFile = open(inputName, "r")
        
        # Do nothing else if empty lines, ...
        if (fault == "\n"):
            continue
        # ... or any comments
        if (fault[0] == "#"):
            continue

        # Removing the the newlines at the end and then output it to the txt file
        fault = fault.replace("\n", "")
        outputFaultFile.write(fault + '\n')

        # Removing spaces
        fault = fault.replace(" ", "")

        lineSpliced = fault.split("-") # splicing the line at the dash sign to get the gate output wire

        # Runs the simulator for each line of the input file
        for line in inputFile:
            # Initializing output variable each input line
            output = ""

            # Do nothing else if empty lines, ...
            if (line == "\n"):
                continue
            # ... or any comments
            if (line[0] == "#"):
                continue

            # Removing the the newlines at the end and then output it to the txt file
            line = line.replace("\n", "")
            outputFaultFile.write(line)

            # Removing spaces
            line = line.replace(" ", "")
            
            print("\n before processing circuit dictionary...")
            # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
            # printCkt(circuit)
            print(circuit)
            print("\n ---> Now ready to simulate INPUT = " + line)
            circuit = inputRead(circuit, line)
            # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
            # printCkt(circuit)
            print(circuit)


            if circuit == -1:
                print("INPUT ERROR: INSUFFICIENT BITS")
                outputFaultFile.write(" -> INPUT ERROR: INSUFFICIENT BITS" + "\n")
                # After each input line is finished, reset the netList
                circuit = newCircuit
                print("...move on to next input\n")
                continue
            elif circuit == -2:
                print("INPUT ERROR: INVALID INPUT VALUE/S")
                outputFaultFile.write(" -> INPUT ERROR: INVALID INPUT VALUE/S" + "\n")
                # After each input line is finished, reset the netList
                circuit = newCircuit
                print("...move on to next input\n")
                continue

            circuit = basic_sim(circuit, lineSpliced, 2)
            print("\n *** Finished simulation - resulting circuit: \n")
            # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
            # printCkt(circuit)
            print(circuit)     

            for y in circuit["OUTPUTS"][1]:
                if not circuit[y][2]:
                    output = "NETLIST ERROR: OUTPUT LINE \"" + y + "\" NOT ACCESSED"
                    break
                output = str(circuit[y][3]) + output

            print("\n *** Summary of simulation: ")
            print(line + " -> " + output + " written into output file. \n")
            outputFaultFile.write(" -> " + output + "\n")
            curr_bad_output[line] = output

            # After each input line is finished, reset the circuit
            print("\n *** Now resetting circuit back to unknowns... \n")
        
            for key in circuit:
                if (key[0:5]=="wire_"):
                    circuit[key][2] = False
                    circuit[key][3] = 'U'

            print("\n circuit after resetting: \n")
            # Uncomment the following line, for the neater display of the function and then comment out print(circuit)
            # printCkt(circuit)
            print(circuit)

            print("\n*******************\n")
            inputFile.close

        detect_map[fault] = curr_bad_output
        curr_bad_output = {}
    print(detect_map)
    outputFaultFile.close
    #exit()
    fault_sim(bench, preserver, inputFault, good_output, detect_map)


if __name__ == "__main__":
    main()