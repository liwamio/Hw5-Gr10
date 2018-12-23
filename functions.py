
# coding: utf-8

# In[ ]:


from collections import defaultdict
import networkx as nx
import pandas as pd
import operator
import math
import os 
import json
import numpy as np

def create_graph():
    global G
    G = nx.DiGraph()
    
    with open('wiki-topcats-categories.txt') as f: 
        categories = f.read()
    with open('wiki-topcats-page-names.txt') as f: 
        page_names = f.read()
    
    c = categories.split('\n')
    cat_dict = create_nodes(c, page_names)
    create_edges()    
    return G, cat_dict

    
def create_nodes(c, page_names): 
    cat_dict = defaultdict(list)
    for i in c: 
        l = i.split(";")
        try: 
            pages = [int(v) for v in l[1].split()]
            if(len(pages) >= 3500):
                G.add_nodes_from(pages)            
                for k in G.nodes(): 
                    G.nodes[k]['Category'] = l[0].split(":")[1]   
                    G.nodes[k]['page_Name'] = page_names[k]               

                cat_dict[l[0].split(":")[1]] = pages    
        except: 
            continue 
    with open('category_cleaned.json', 'w') as f: 
        json.dump(cat_dict,f)
    return cat_dict

    
# Create links between nodes using 'wiki-topcats-reduced.txt'
def create_edges(): 
    with open('wiki-topcats-reduced.txt') as f: 
        nodes = f.read()
    rows = nodes.split('\n')
    for n in rows:     
        ns = n.split('\t')    
        try: 
            G.add_edge(int(ns[0]), int(ns[1]))            
        except: 
            continue  

            
def ten_category(cat_dict): 
    cat_ten = defaultdict(list)
    idx = 0
    for c in cat_dict:         
        tempn = {}
        for nodes in cat_dict[c]: 
            tempn[nodes] = len(list(nx.neighbors(G,nodes)))   
        sorted_x = sorted(tempn.items(), key=operator.itemgetter(1), reverse=True)[:500]           

        sorted_nodes = []
        for s in sorted_x:        
            sorted_nodes.append(s[0])        

        cat_ten[c] = sorted_nodes  
        if(idx == 9): 
            break
        idx += 1  
    with open('category_10.json', 'w')as f: 
        json.dump(cat_ten, f)
    return cat_ten


def remove_duplicates(cat_ten):     
    catagories = list(cat_ten.keys())

    for i in range(len(catagories)-1): 
        for j in range(2,len(catagories)):
            intersection = set(cat_ten[catagories[i]]) & set(cat_ten[catagories[j]])
            for k in intersection: 
                set(cat_ten[catagories[j]]).remove(k)            
    with open('category_10.json', 'w') as f: 
        json.dump(cat_ten,f)
        

def find_shortest_path(initial_nodes, destination_nodes):   

    #dictionary to save distance of each node from the input category to nodes in other categories
    path_dicts = defaultdict(list)

    #we will find the distance between each node from the input category to other categories
    for i_n in initial_nodes:      

        #dictionary to save all nodes
        path_dict = defaultdict(list)

        #set all nodes as unvisited and their distance to the input node as infinity
        path_dict = {nodes: [False, math.inf] for nodes in destination_nodes}    
        #set the path of the current node being traversed in the input category to its own done as 0
        path_dict[i_n] = [False, 0]   

        #set our node with a minimum distance as infinity
        min_node = destination_nodes[0]
        idx = 0
        while(True):
            #get nodes that are unvisited
            false_path_dict = {p: [False, path_dict[p][1]] for p in path_dict if path_dict[p][0] == False}
            try: 
                #from unvisited nodes get a node with a minimum distance
                min_node = min(false_path_dict.items(), key=operator.itemgetter(1))[0]                                        
            except: 
                #if all nodes have been visited break out, iterate for the next node in the input category
                break

            #set the mode with the minimum distance as visited 
            path_dict[min_node][0] = True

            #find the neighbours of the node with the minimum distance
            ngh = nx.neighbors(G, min_node)       

            #traverse through all the neighbor nodes
            for n in ngh:              
                '''
                If the node has not been visited continue.
                If the node has been visited then the shortest distance to that node has already been found. 
                '''            
                if(n in false_path_dict):                                

                #if(path_dict[n][0] != True): # just check if in false_path_dict
                    '''
                    check if the distance to the node is infinity, 
                    if so assign the distance as the distance to the node with the minimum distance plus 1. 
                    Here we only add 1 because our edges aren't weighted. 
                    '''

                    '''
                    If the distance to the node is not infinity, then check if the path to the distance is less than 
                    the path to the node with the minimum path plus 1, if so update the distance.
                    '''
          
                    if((path_dict[min_node][1] + 1) < path_dict[n][1]):                     
                        path_dict[n][1] = path_dict[min_node][1] + 1        
            '''
            After breaking out of the inner loop: caclulating the distance between the node in the input category 
            and other nodes in other categories, save the distance in another dictionary,
            and repeat it for other nodes in the input category.
            '''
            path_dicts[i_n] = path_dict
            
    os.mkdir('data')
    with open('data/dict.json', 'w') as outfile:
        json.dump(path_dicts, outfile, indent=2)
        
    return path_dicts


def computeDist(src, dest, dic):
    try:
        return (dic[str(src)][str(dest)][1])
    except:
        if src == dest:
            return 0
        else:
            return np.inf  
        

'''
We loop through the nodes of both categories to find all possible shortest path between each node in the categories. 
We will use the `computeDist` function to find the distance between two nodes. 
'''


def shortest_path(node_C0, node_Ci, cat_ten, dic): 
    shortest_paths = []
    for i in cat_ten[node_C0]:        
        for j in cat_ten[node_Ci]:            
            shortest_paths.append(computeDist(i,j, dic))
    return shortest_paths


def distance(C0, Ci, cat_ten, dic):    
    return (np.median(shortest_path(C0, Ci, cat_ten, dic)))


def update_score(G2, edges, Ci, cat_ten):
    # updating the graph with another category
    nodes = set(cat_ten[Ci])
    G2.add_nodes_from(nodes)
    for edge in edges:
        if edge[0] in G2.nodes() and edge[1] in G2.nodes():
            G2.add_edge(edge[0], edge[1])
    # updating the score
    scores = nx.get_node_attributes(G,'score') # the previous scores
    for node in nodes:
        score_node = 0
        for edge in G2.in_edges(node):
            if edge[0] in scores:
                score_node += scores[edge[0]]
            else:
                score_node += 1
        G2.add_node(node, score = score_node)
        
        
def rank(sorted_median, scores, cat_ten): 
    rank = []
    for Ci in sorted_median:
        for node in scores:
            if node[0] not in rank and node[0] in cat_ten[Ci[0]]:
                rank.append(node[0])
    return rank

