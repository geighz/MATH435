import numpy as np
import random as rd
import matplotlib.pyplot as plt
import networkx as nx
import math
import copy
import sys
from itertools import count
from IPython import display

"""
Created by Geigh Zollicoffer, Nick Verdoni, Masen Bachelda, Roderick Riley
Math 435 MCMC project

Simulates valid districting plans over a voter distribution
in order to test the fairness of a initial plan.
"""

def colorful_vertex_plot(g, pos, attr, node_size = 75, cmap = plt.cm.jet, 
                         plot_title = ''):
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 6))
    ax.set_title(plot_title)
    ax.axis('Off')
    groups = set(nx.get_node_attributes(g, attr).values())
    mapping = dict(zip(sorted(groups),count()))
    nodes = g.nodes()
    colors = [mapping[g.node[n][attr]] for n in nodes]
    ec = nx.draw_networkx_edges(g, pos, alpha=0.2)
    nc = nx.draw_networkx_nodes(g, pos, nodelist=nodes, node_color=colors, 
                                with_labels=False, node_size = node_size, 
                                cmap = cmap)

def round_sf(number, significant):
    return round(number, significant - len(str(number)))

def is_valid_swap(x, y,G):
    x_dist = G.nodes[x]['district']
    y_dist = G.nodes[y]['district']
    Dx = G.subgraph([node for node in G.nodes if G.nodes[node]['district'] == 
                     x_dist and not node == x])
    Dy = G.subgraph([node for node in G.nodes if G.nodes[node]['district'] == 
                     y_dist and not node == y])
    for comp in nx.connected_components(Dx):
        if set(G.neighbors(y)).intersection(set(comp))== set():
            return False
    for comp in nx.connected_components(Dy):
        if set(G.neighbors(x)).intersection(set(comp))== set():
            return False
    return True


def updateSwaps(G,x,y):
    
    nodes_to_check = [x]+[y]+list(G.neighbors(x))+list(G.neighbors(y))
    for node in G.neighbors(x):
        for nbr in G.neighbors(node):
            nodes_to_check.append(nbr)
    for node in G.neighbors(y):
        for nbr in G.neighbors(node):
            nodes_to_check.append(nbr)
    nodes_to_check = list(set(nodes_to_check))
    #Adding to Swaps for the corresponding node
    for z in nodes_to_check:
        G.nodes[z]['swaps'] = []
        for node in nodes:
            if G.nodes[node]['district'] == G.nodes[z]['district']:
                pass
            else:
                if is_valid_swap(z, node,G):
                    G.nodes[z]['swaps'].append(node)
                    if z not in G.nodes[node]['swaps']:
                        G.nodes[node]['swaps'].append(z)
                else:
                    if z in G.nodes[node]['swaps']:
                        G.nodes[node]['swaps'].remove(z)

    
    

class gerrymanderDataTable:
    
    def __init__(self,amountOfDist,distSize,graph):
        #per
        self.winThresh = math.floor(distSize/2.0)+1;
        #Current wins within a district
        self.districtWinsPool = dict.fromkeys((range(0,amountOfDist)));
        #Current wins for each party throughout the graph.
        self.partyWins = dict.fromkeys((range(0,amountOfDist)));
        #Amount of districts won for a party
        self.seatWins = [0] * (amountOfDist+1)
        self.setWinsPool(graph);
            
    def setWinsPool(self,graph):
        
        '''
        Set every key to 0 meaning blue is currently winning 0 seats
        in each district.
        '''
        for district in self.districtWinsPool:
            self.districtWinsPool[district] = [0]
        '''
        This is all time party wins within a certain district
        First item is blue wins, second is white wins,
        second is not currently being used since we 
        are only displaying data of the blue party.
        '''
        for district in self.partyWins:
        
            self.partyWins[district] = [0,0]
            
        #This is all time wins for a [district], 0 means no seats.
        for district in self.seatWins:
            self.seatWins[district] = 0
        
        
        
        #Just setting up what the win total currently looks like:
        for node in graph.nodes:
            dist = graph.nodes[node]['district'];
            if(graph.nodes[node]['party']==0):
                self.districtWinsPool[dist][0] +=1
                 
        blueSeats = 0;
        for district in self.districtWinsPool:
            if(self.districtWinsPool[district][0]>=self.winThresh):
                self.partyWins[district][0] +=1
                blueSeats+=1
        self.seatWins[blueSeats] = 1
            
    def getSeatWins(self):
        return self.seatWins
    
    def updateTable(self,swapX,swapY,g):
        
        '''
        Gaining data between two precincts that were swapped
        between district X and district Y, hence the name
        swap X and swap Y
        '''
        
        xDist = g.nodes[swapX]['district']
        xParty = g.nodes[swapX]['party']
        yDist = g.nodes[swapY]['district']
        yParty = g.nodes[swapY]['party']
        
        '''
        Update table on if 0/blue party won a precinct,
        If the party won: decrease previous district total number
        of blue/0 party wins by 1 and increase new district's 
        total number of blue/0 precinct wins by 1.
        '''
        
        if(xParty == 0):
            self.districtWinsPool[xDist][0] +=1
            self.districtWinsPool[yDist][0] -=1
            
        if(yParty == 0):
            self.districtWinsPool[yDist][0] +=1
            self.districtWinsPool[xDist][0] +=-1
        
        blueSeats = 0;
        
        for district in self.districtWinsPool:
            if(self.districtWinsPool[district][0]>=self.winThresh):
                blueSeats+=1
       
        self.seatWins[blueSeats] +=1
    
":::::::::::::::::::::This is where the main Driver will Run::::::::::::::::::"

'''
These are settings that a user can use to manipulate the size 
of the districting plans.
'''
distSize = 5;
amountOfDist = 5;     

#Our Toy graph coresponding to toy parameters.
g = nx.grid_graph(dim=[amountOfDist,distSize])
validSwaps = [];

#setting up the graph with certain attributes
blueCounter = 0
for i in range(0,amountOfDist):
    for j in range (0,distSize):
        g.nodes[(j,i)]['district']=i
        g.nodes[(j,i)]['swaps']=[]
        
        #Random Party Assignment.
        randint = rd.randint(0,1)
        g.nodes[(j,i)]['party']= randint
        if(randint == 0):
            blueCounter +=1

votePer = (blueCounter/(distSize*amountOfDist))*100
print("blue holds %",votePer,"Percent of the vote")


'''
Gathers and appends all possible swaps for each precinct
'''

pos = dict((node, node) for node in g.nodes)
nodes = list(g.nodes)
for i in range(len(nodes)):
    for j in range(i, len(nodes)):
        if g.nodes[nodes[i]]['district']==g.nodes[nodes[j]]['district']:
            pass
        else:
            if is_valid_swap(nodes[i],nodes[j],g):
                g.nodes[nodes[i]]['swaps'].append(nodes[j])
                g.nodes[nodes[j]]['swaps'].append(nodes[i])

#Halts program until user hits enter.
input("Press Enter to continue...")
nodes = list(g.nodes)

#Our object that will keep track of statistics.
gdt = gerrymanderDataTable(amountOfDist,distSize,g);

#Running the update on valid swaps and making the swap.
swaps = []
for node in nodes:
    for swap in g.nodes[node]['swaps']:
        if{node,swap} not in swaps:
            swaps.append({node,swap})
            
someArr = gdt.getSeatWins()
x = list(range(0,amountOfDist+1,1))
x_pos = [i for i, _ in enumerate(x)]
plt.bar(x_pos, someArr, color='green')
plt.xlabel("Seats Won")
plt.ylabel("Frequency")
plt.title("Seats won by blue")
plt.xticks(x_pos, x)
            

'''
This section of the data will make the random swaps
while keeping statistics of districting plans. 
This is the main part of the code with an
optional animated bar plot. 
'''

#iterations: a user can manipulate n for any amount of swaps.
n = 100
t = 0
p= n*.01
enumX = list(range(0,amountOfDist+1,1))
while t<n:
    #Optional percentage tracker/animated bar plot
    if t%p==0:
        per = (t/n)*(100)
        sys.stdout.write("\r%f%%" %per)
        sys.stdout.flush()
        if t%10 ==0:
            plt.clf()
            seatWins = gdt.getSeatWins()
            x_pos = [i for i, _ in enumerate(enumX)]
            plt.bar(x_pos, seatWins, color='green')
            display.display(plt.gcf())
            display.clear_output(wait=True)
    #Part of the code that handles swaps:
    proposal = list(rd.choice(swaps))
    x = proposal[0]
    y = proposal[1]
    proposal_G = copy.deepcopy(g)
    x_dist = proposal_G.nodes[x]['district']
    y_dist = proposal_G.nodes[y]['district']
    proposal_G.nodes[x]['district'] = y_dist
    proposal_G.nodes[y]['district'] = x_dist
    error = updateSwaps(proposal_G,x,y)
    new_swaps = []
    for node in nodes:
        for swap in proposal_G.nodes[node]['swaps']:
            if {node,swap} not in new_swaps:
                new_swaps.append({node,swap})
    p = min([len(swaps)/len(new_swaps),1])
    coin = np.random.binomial(1,p)
    #Gives a probability on staying with same districting plan,
    #once valid swaps are calculated.
    if coin == 1:
        g = proposal_G
        swaps = new_swaps
        t+=1
        error = gdt.updateTable(x,y,g) 
    else:
        t+=1
        error = gdt.updateTable(x,x,g) 
    
    
'''
Final output of histogram, votes distribution and exact count
of votes for blue/0 in every district.
'''

seatWins = gdt.getSeatWins()
x = list(range(0,amountOfDist+1,1))
x_pos = [i for i, _ in enumerate(x)]
plt.bar(x_pos, seatWins, color='green')
plt.xlabel("Seats Won")
plt.ylabel("Frequency")
plt.title("Seats won by blue")
plt.xticks(x_pos, x)
print("\n")
for i in range(0,amountOfDist+1):
    print("Blue won ",i,"seats ",seatWins[i],"times.")  
colorful_vertex_plot(g, pos, 'party', node_size=500)

