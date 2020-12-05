# Bayesic: This program takes in a number of parent and descendant nodes
# from the command line and, according to their assigned probabilities,
# samples the Bayesian network a fixed number of times, appending a note
# for each node that takes on the value 1 in the sample.

from music21 import *
import random
from tkinter import *
from tkinter.ttk import *

# each node will be on or off with prob p

def bernoulli(p):
    event = random.random() < p
    if event: 
        return 1
    else: 
        return 0

# begin interacting with user

parents = []
descendants = {}
tiers = {}
probs = {}
freqs = {}

inp = "Beginning..."
print(inp)

# get all parents

while True:
    parent = input("Specify one parent node at a time.\n Enter the label of the node and its probability, comma-delimited (e.g. Lara,0.3) , then hit ENTER.\n Hit ENTER without input when all parents have been specified.")

    if len(parent) == 0: # ENTER has been hit; we can stop
        break

    comma = parent.find(',')

    if comma == -1:
        print("The format is label,prob without spaces.")
        continue

    label = parent[:comma]
    prob = float(parent[comma + 1:])
    probs[label] = prob
    parents.append(label)
    
tiers[0] = parents

# get all descendants

cont = "yes"
tierno = 1

while tierno <= 4:
    if cont != "yes":  # if user wants no more tiers
        break
        
    print("Getting descendants for tier " + str(tierno) + '.')
    print("Please make sure you only condition on nodes of the previous tier. All possible parents are:")
    for p in tiers[tierno-1]:
        print(p)
        
    tiers[tierno] = []
        
    while True:
        desc = input("Specify one node at a time. Enter the label of the node and, after a hyphen, the labels of its parents, comma-delimited (e.g. Ian-Lara,Coleman), then hit ENTER.\n At most two parents are allowed for simplicity; all parents must be in the preceding tier.\n Hit ENTER without input when all nodes have been specified.")
        if len(desc) == 0:
            break

        hyphen = desc.find('-')
        if hyphen == -1:
            print("The format is desc-parent,parent.")
            continue

        ps = desc[hyphen + 1:]
        comma = ps.find(',')

        if comma == -1:
            parent = ps
            if parent not in tiers[tierno - 1]:
                print("You can only use parent nodes from the preceding tier.")
                continue
            label = desc[:hyphen]
            if label in list(descendants.keys()):
                print("Descendants must have unique names.")
                continue
            tiers[tierno].append(label)
            descendants[label] = [parent]

        else:
            parent1 = ps[: comma]
            parent2 = ps[comma + 1:]

            if parent1 not in tiers[tierno - 1] or parent2 not in tiers[tierno - 1]:
                print("You can only use parent nodes from the preceding tier.")
                continue

            if parent2.find(',') != -1:
                print("Only two parents.")
                continue

            label = desc[:hyphen]
            tiers[tierno].append(label)
            descendants[label] = [parent1, parent2]
            
    tierno += 1
    cont = input("Would you like to add another tier? Answer yes or no.")
        
# get conditional probabilities for descendants

for desc, plist in descendants.items():
    if len(plist) == 1:
        prob0_label = desc + '_' + plist[0] + '0'
        prob1_label = desc + '_' + plist[0] + '1'
        
        prob0 = input("Enter the probability of " + desc + '|' + plist[0] + '= 0.')
        prob1 = input("Enter the probability of " + desc + '|' + plist[0] + '= 1.')
        
        probs[prob0_label] = float(prob0)
        probs[prob1_label] = float(prob1)
    
    else:
        prob00_label = desc + '_' + plist[0] + '0' + plist[1] + '0'
        prob01_label = desc + '_' + plist[0] + '0' + plist[1] + '1'
        prob10_label = desc + '_' + plist[0] + '1' + plist[1] + '0'
        prob11_label = desc + '_' + plist[0] + '1' + plist[1] + '1'
        
        prob00 = input("Enter the probability of " + desc + '|' + plist[0] + '= 0,'+ plist[1] + '= 0.')
        prob01 = input("Enter the probability of " + desc + '|' + plist[0] + '= 0,'+ plist[1] + '= 1.')
        prob10 = input("Enter the probability of " + desc + '|' + plist[0] + '= 1,'+ plist[1] + '= 0.')
        prob11 = input("Enter the probability of " + desc + '|' + plist[0] + '= 1,'+ plist[1] + '= 1.')
        
        probs[prob00_label] = float(prob00)
        probs[prob01_label] = float(prob01)
        probs[prob10_label] = float(prob10)
        probs[prob11_label] = float(prob11)

# assign frequencies to each parent

for parent in parents:
    freqs[parent] = input("What is the frequency assigned to the parent node " + parent + " ?")
    
ngens = input("How many times will you traverse the Bayesian network?")

# start making music!

waterfalls = stream.Stream()
amp = 90
amp_mod = 0.9 # 90% of volume for each tier
w0 = 0.3 # if parent state 0, this much of it goes into average
w1 = 1
nodes = parents + list(descendants.keys())
nodestates = {}

for i in range(int(ngens)):
    if i > 0:
        r = note.Rest() # a rest between each generation
        r.duration.quarterLength = 0.33
        waterfalls.append(r)
    
    #sampling time!
    print("Sample ", i)
    
    for parent in parents:
        prob = probs[parent]
        state = bernoulli(prob)
        nodestates[parent] = state
        if state != 0: #if parent on
            f = note.Note()
            f.pitch.frequency = float(freqs[parent])
            f.volume.velocity = amp
            f.duration.quarterLength = 0.33
            waterfalls.append(f)
    
    for tierno, tiernodes in tiers.items():
        if tierno == 0:
            continue
            
        for node in tiernodes:
            node_ps = descendants[node] # all parents this node is conditioned on
            cond = ""
            nodef = 0
            
            for p in node_ps:
                cond += (p + str(nodestates[p]))
                if nodestates[p] == 0:
                    weight = w0
                else:
                    weight = w1
                    
                nodef += float(freqs[p]) * weight
            
            nodef /= len(node_ps) # weighted average
            label = node + '_' + cond
            
            prob_node = probs[label]
            freqs[node] = nodef
            state = bernoulli(prob_node)
            nodestates[node] = state
            
            if state != 0:
                f = note.Note()
                f.pitch.frequency = nodef
                f.volume.velocity = amp * amp_mod ** tierno
                f.duration.quarterLength = 0.166666
                waterfalls.append(f)
        
    # nodestates is the whole sample now!
    print(nodestates)

filename = str(len(parents)) + '_' + str(ngens) + '_' + str(len(list(descendants.keys()))) + '.mid'
waterfalls.write('midi', filename)