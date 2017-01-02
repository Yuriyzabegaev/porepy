# -*- coding: utf-8 -*-

import numpy as np
import scipy.sparse as sps

from core.grids.grid import Grid
from utils import matrix_compression

#------------------------------------------------------------------------------#

def generateCoarseGrid( g, subdiv ):
    subdiv = np.asarray( subdiv )
    assert( subdiv.shape[0] == g.num_cells )

    cell_faces = np.empty( 0, dtype = np.int )
    cells = np.empty( 0, dtype = np.int )
    orient = np.empty( 0, dtype = np.float )

    face_nodes = np.empty( 0, dtype = np.int )
    nodes = np.empty( 0, dtype = np.int )
    # there is no check for disconnected cells

    cells_list = np.unique( subdiv )
    num_nodes_per_face = g.face_nodes.indptr[1:] - g.face_nodes.indptr[:-1]
    face_node_ind = matrix_compression.rldecode(np.arange(
                                              g.num_faces), num_nodes_per_face)

    for cellId, cell in enumerate( cells_list ):
        cells_old = np.where( subdiv == cell )[0]
        faces_old, _, orient_old = sps.find( g.cell_faces[:, cells_old] )

        # faces
        mask = np.zeros( faces_old.shape[0], dtype=np.bool )
        mask[ np.unique( faces_old, return_index=True )[1] ] = True
        index = np.array([ np.where( faces_old == f )[0] \
                                             for f in faces_old[~mask]]).ravel()
        faces_new = np.delete( faces_old, index )
        cell_faces = np.r_[ cell_faces, faces_new ]
        cells = np.r_[ cells, cellId*np.ones(faces_new.shape[0], dtype = np.int) ]
        orient = np.r_[ orient, np.delete( orient_old, index ) ]

        # nodes
        mask = np.sum( [ face_node_ind == f for f in faces_new ], \
                       axis = 0, dtype = np.bool )
        #nodes_new, rep, _ = sps.find( g.face_nodes[:, faces_new] )
        face_nodes = np.r_[ face_nodes, face_node_ind[ mask ] ]
        nodes_new = g.face_nodes.indices[ mask ]
        nodes = np.r_[ nodes, nodes_new ]

    # Rename the faces
    cell_faces_unique = np.unique( cell_faces )
    cell_faces_id = np.arange( cell_faces_unique.shape[0] )
    cell_faces = np.array( [ cell_faces_id[ np.where( cell_faces_unique == f )[0] ] \
                                                 for f in cell_faces ] ).ravel()

    shape = ( cell_faces_unique.shape[0], cells_list.shape[0] )
    cell_faces =  sps.csc_matrix( (orient, (cell_faces, cells)), shape = shape )

    # Rename the nodes
    face_nodes = np.array( [ cell_faces_id[ np.where( cell_faces_unique == f )[0] ] \
                                                 for f in face_nodes ] ).ravel()
    nodes_list = np.unique( nodes )
    nodes_id = np.arange( nodes_list.shape[0] )
    nodes = np.array( [ nodes_id[ np.where( nodes_list == n )[0] ] \
                                                      for n in nodes ] ).ravel()

    shape = ( nodes_list.shape[0], cell_faces_unique.shape[0] )
    face_nodes =  sps.csc_matrix( (np.ones( nodes.shape[0], dtype = np.bool),\
                                  (nodes, face_nodes) ), shape = shape )

    name = g.name + "_coarse"
    return Grid( g.dim, g.nodes[:,nodes_list], face_nodes, cell_faces, name )

#------------------------------------------------------------------------------#
