#! /usr/bin/env python
#                                                      
# 1. Read in an Excel file with a weighted connection matrix,
#    where each row and column represents a region of the brain, and values
#    are a function of how much of the adjacent regions' boundaries are shared. 
# 2. Convert the matrix to a NetworkX weighted graph.
# 3. Create a colormap for the number of brain regions, with hues that are 
#    uniformly distributed about a cylindrical color space, such as CIELch.
# 4. Plot the colormap, the graph, or output a modified XML file.
#
# The graph is plotted as a collection of subgraphs, with each subgraph 
# representing a collection of adjacent regions, and assigned adjacent colors
# in the color space.  
# All permutations are computed for the colors of each subgraph, 
# and the winning permutation is the one that maximizes the
# discriminability of the colors of nodes of highest degree.
# This is performed by mulfiplying the connection matrix for each subgraph
# by the color difference matrix for each permutation. 
#
# (c) Copyright 2010 . arno klein . arno@binarybottle.com . MIT license
#

import sys
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import re
import itertools
from colormath.color_objects import LCHuvColor
from elementtree import ElementTree as et
import xlrd

# Choose one procedure to run:
plot_colormap = 0
plot_subcolormaps = 0
plot_graph = 0
plot_subgraphs = 0
make_xml = 1

save_plots = 0

# Files
in_dir = 'input/'
out_dir = 'output/'
out_images = out_dir
in_xml = in_dir + 'parcLabels.xml'
out_xml = out_dir + 'parcLabels.xml'
in_table = in_dir + 'average_parc_Connectivity.xls'
in_table2 = in_dir + 'average_parc_Connectivity_subgroups.xls'
row1 = 1  # first row with data
col1 = 5  # first column with data
everyother = 2  # use <everyother> alternate rows/columns;
                # set to 2 for redundant labels across brain hemispheres
                    
# Color parameters
#Lumas_init = np.array([60,75,90])
init_angle = 0 #22.5
Lumas_init = np.arange(50,100,20)  # vary luminance values for adjacent colors
chroma = 70  # color "saturation" level
color_by_sublobe = 1  # group by sublobe -- else by assigned number
use_small_groups = 0  # if color_by_sublobe=0 & want faster output
repeat_hues = 1

# Edge parameters
use_existing_weights = 0  # Use weights

# Debugging
debug_subgraph = 0
debug_lumas = 0

# Convert weighted connection matrix to weighted graph
if use_small_groups:
    book = xlrd.open_workbook(in_table2)
else:
    book = xlrd.open_workbook(in_table)
sheet = book.sheets()[0]
roi_abbrs = sheet.col_values(0)[1:sheet.ncols:everyother]
roi_abbrs = [str(s).strip() for s in roi_abbrs]
if color_by_sublobe:
    roi_numbers = sheet.col_values(2)[1:sheet.ncols:everyother] 
    roi_numbers = [str(s).strip() for s in roi_numbers]
else:
    roi_numbers = sheet.col_values(3)[1:sheet.ncols:everyother] 
if color_by_sublobe:
    code_min = min(roi_numbers)
    code_max = max(roi_numbers)
    code_min = np.int(code_min.split('.')[0] + code_min.split('.')[1])
    code_max = np.int(code_max.split('.')[0] + code_max.split('.')[1])
else:
    code_min = min(roi_numbers)
    code_max = max(roi_numbers)
code_step = 1
    
iA = 0
A = np.zeros(((sheet.nrows-row1)/everyother,(sheet.ncols-col1)/everyother))
for irow in range(row1,sheet.nrows,everyother):
    Arow = [s.value for s in sheet.row(irow)[col1:]]
    A[iA] = Arow[0:len(Arow):everyother]
    iA += 1
A = A/np.max(A)  # normalize weights
G = nx.from_numpy_matrix(A)
Ntotal = G.number_of_nodes()
for inode in range(Ntotal):
    G.node[inode]['abbr'] = roi_abbrs[inode] 
    if color_by_sublobe:
        G.node[inode]['code'] = roi_numbers[inode].split('.')[0] + \
                                roi_numbers[inode].split('.')[1]
    else:
        G.node[inode]['code'] = roi_numbers[inode]

# Secondary parameters
if debug_lumas:
    color_angle = 0 
else:
    color_angle = 360.0 / Ntotal
    if repeat_hues:
        nLumas = len(Lumas_init)
        nangles = np.ceil(Ntotal / np.float(nLumas))
        color_angle = nLumas * color_angle
    else: 
        nangles = Ntotal
        
# Plot the colormap for the whole graph    
if plot_colormap:
    fig1 = plt.figure(figsize=(5,10))
    # Define colormap as uniformly distributed colors in CIELch color space
    Lumas = Lumas_init.copy()
    while len(Lumas) < Ntotal: 
        Lumas = np.hstack((Lumas,Lumas_init))
    if debug_lumas:
        hues = init_angle*np.ones(Ntotal)
    else:
        hues = np.arange(init_angle, init_angle + nangles*color_angle, color_angle)
        if repeat_hues:
            hues = np.hstack((hues * np.ones((nLumas,1))).transpose())
    for iN in range(Ntotal):
        ax = plt.subplot(Ntotal, 1, iN+1)
        plt.axis("off")
        lch = LCHuvColor(Lumas[iN], chroma, hues[iN]) #print(lch)
        rgb = lch.convert_to('rgb', debug=False)
        plt.barh(0,50,1,0, color=[rgb.rgb_r/255.,rgb.rgb_g/255.,rgb.rgb_b/255.])
    if save_plots:
        plt.savefig(out_images + "braincolormap.png")
     
# Plot graph
if plot_graph:
    labels={}
    for i in range(Ntotal):
        labels[i] = G.node[i]['abbr']
    pos = nx.graphviz_layout(G,prog="neato")
    #pos = nx.spring_layout(G)
    #colors = [np.int(s) for s in G.number_of_edges()*np.ones(G.number_of_edges())]
    #nx.draw(G,pos,node_color='#333399',node_size=600,width=2,edge_color=colors,edge_cmap=plt.cm.Blues,with_labels=False)
    nx.draw(G,pos,node_color='#333399',node_size=600,width=1,with_labels=False)
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_color='black')
    plt.axis('off')
    #plt.show(); sys.exit()
    
if make_xml:
    tree = et.ElementTree(file=in_xml)
    
# Loop through subgraphs
if plot_graph + plot_subcolormaps + plot_subgraphs + make_xml > 0:
    run_permutations = 1
    for code_start in range(code_min,code_max+code_step,code_step):   
        glist = [n for n,d in G.nodes_iter(data=True) \
                   if (np.int(d['code'])>=code_start) and \
                      (np.int(d['code'])<code_start+code_step)] 
        N = len(glist)
        if N > 0:
            g = G.subgraph(glist)
            
            # Define colormap as uniformly distributed colors in CIELch color space
            Lumas = Lumas_init.copy()
            while len(Lumas) < N: 
                Lumas = np.hstack((Lumas,Lumas_init))
        
            if repeat_hues:
                nangles_g = np.ceil(N / np.float(nLumas))
            else: 
                nangles_g = N
            hues = np.arange(init_angle, init_angle + nangles_g*color_angle, color_angle)
            if repeat_hues:
                hues = np.hstack((hues * np.ones((nLumas,1))).transpose())

            init_angle += nangles_g*color_angle
        
            # Compute the differences between every pair of colors in the colormap
            if run_permutations:
                # Convert subgraph into an adjacency matrix (1 for adjacent pair of regions)
                neighbor_matrix = np.array(nx.to_numpy_matrix(g,nodelist=glist))
                if use_existing_weights:
                    pass
                else:
                    neighbor_matrix = (neighbor_matrix > 0).astype(np.uint8)
                    weight_by_degree = 0  # Assign weights by node degree
                    if weight_by_degree:
                        matrix_sum = np.sum(neighbor_matrix, axis=0)
                        neighbor_matrix = neighbor_matrix * (matrix_sum * np.ones((N,N))).transpose()
                
                # Compute permutations of colors and color pair differences
                DEmax = 0
                permutations = [np.array(s) for s in itertools.permutations(range(0,N),N)]
                permutation_max = np.zeros(N)
                for ipermutations in range(len(permutations)):
                    permutation = permutations[ipermutations]
                    color_delta_matrix = np.zeros(np.shape(neighbor_matrix))   
                    for i1, icolor1 in enumerate(permutation):
                        lch1 = LCHuvColor(Lumas[icolor1],chroma,hues[icolor1]) 
                        for i2, icolor2 in enumerate(permutation):
                            if (i2 > i1) and (neighbor_matrix[i1,i2] > 0):
                                lch2 = LCHuvColor(Lumas[icolor2],chroma,hues[icolor2])
                                DE = lch1.delta_e(lch2, mode='cie2000')
                                color_delta_matrix[i1,i2] = DE   
                    DE = np.sum((color_delta_matrix * neighbor_matrix))
                    # Store the color permutation with the maximum adjacency cost
                    if DE > DEmax:
                        DEmax = DE
                        permutation_max = permutation
                        #color_delta_matrix_max = color_delta_matrix
            # Plot the reordered colormap for the subgraph    
            if plot_subcolormaps:
                fig3 = plt.figure(figsize=(5,10))
                fig3.subplots_adjust(top=0.99, bottom=0.01, left=0.2, right=0.99)
                for iN in range(N):
                    ax = plt.subplot(N, 1, iN+1)
                    plt.axis("off")
                    ic = np.int(permutation_max[iN])
                    lch = LCHuvColor(Lumas[ic],chroma,hues[ic]) #print(lch)
                    rgb = lch.convert_to('rgb', debug=False)
                    plt.barh(0,50,1,0, color=[rgb.rgb_r/255.,rgb.rgb_g/255.,rgb.rgb_b/255.])
                if save_plots:
                    plt.savefig(out_images + "braincolormap_subgraph" + str(g.node[g.nodes()[0]]['code']) + ".png")
                plt.show()
                    
            # Color subgraphs
            if plot_graph:
                for iN in range(N):
                    ic = np.int(permutation_max[iN])
                    lch = LCHuvColor(Lumas[ic],chroma,hues[ic]) #print(lch)
                    rgb = lch.convert_to('rgb', debug=False)
                    color = [rgb.rgb_r/255.,rgb.rgb_g/255.,rgb.rgb_b/255.]
                    nx.draw_networkx_nodes(g,pos,node_size=600,nodelist=[g.node.keys()[iN]],node_color=color)

            # Draw a figure of the colored subgraph
            if plot_subgraphs:
                labels={}
                for iN in range(N):
                    labels[g.nodes()[iN]] = g.node[g.nodes()[iN]]['abbr']
                pos = nx.graphviz_layout(g,prog="neato")
                #pos = nx.spring_layout(G)
                #colors = [np.int(s) for s in g.number_of_edges()*np.ones(g.number_of_edges())]
                #nx.draw(g,pos,node_size=600,width=2,edge_color=colors,edge_cmap=plt.cm.Blues,with_labels=False)
                nx.draw(g,pos,node_size=1200,width=1,with_labels=False)
                nx.draw_networkx_labels(g,pos,labels,font_size=12,font_color='black')
                plt.axis('off')
                for iN in range(N):
                    ic = np.int(permutation_max[iN])
                    lch = LCHuvColor(Lumas[ic],chroma,hues[ic]) #print(lch)
                    rgb = lch.convert_to('rgb', debug=False)
                    color = [rgb.rgb_r/255.,rgb.rgb_g/255.,rgb.rgb_b/255.]
                    nx.draw_networkx_nodes(g,pos,node_size=1200,nodelist=[g.node.keys()[iN]],node_color=color)
                if save_plots:
                    plt.savefig(out_images + "braincolorsubgraph" + str(g.node[g.nodes()[0]]['code']) + ".png")
                plt.show()
                if debug_subgraph:
                    sys.exit()

            # Generate XML output       
            """
            <LabelList>
            <Label>
              <Name>3rd Ventricle</Name>
              <Number>4</Number>
              <RGBColor>204 182 142</RGBColor>
            </Label>
            """
            if make_xml:
                for iN in range(N):
                    ic = np.int(permutation_max[iN])
                    lch = LCHuvColor(Lumas[ic],chroma,hues[ic]) #print(lch)
                    rgb = lch.convert_to('rgb', debug=False)
                    color = [rgb.rgb_r, rgb.rgb_g, rgb.rgb_b]
                    color = ' '.join([str(s) for s in color])
                    for elem in tree.getiterator()[0]:
                        if g.node[g.nodes()[iN]]['abbr'] in elem.getchildren()[0].text:
                            elem.getchildren()[2].text = color
                            print(g.node[g.nodes()[iN]]['abbr'],color)
                    
if plot_graph:
    if save_plots:
        plt.savefig(out_images + "braincolorgraph.png")

if make_xml:
    tree.write(out_xml)
