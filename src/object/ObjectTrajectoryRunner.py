import bpy

from src.utility.BlenderUtility import get_mesh_objects_with_name
from src.main.Module import Module
from src.utility.Utility import Utility
from src.object.MeshDeformer import MeshModeler

from mathutils import Vector, Euler
import numpy as np
import numpy.polynomial.polynomial as poly
import bmesh
import sys
import numbers
from collections import defaultdict

class ObjectTrajectoryRunner(Module):
    """ 
    Load an object and run it along the predefined trajectory
    """

    def __init__(self, config):
        Module.__init__(self, config)
        self.location_poly = self.config.get_list("poses/location_poly")
        self.rotation_poly = self.config.get_list("poses/rotation_poly")

    # I have no idea why it gives me 3 arguments
    # Maybe it just wants to argue with me
    def mesh_deform_handler(self, scene, sth):
        frame = scene.frame_current

        if frame == 0:
            self.obj = get_mesh_objects_with_name([self.name])[0]
            self.modeler.mesh = self.obj.data

        self.modeler.update_animation(frame)
        self.modeler.apply_transformation()

    def run(self, n_frames):

        file_path = Utility.resolve_path(self.config.get_string("path"))
        self.obj = Utility.import_objects(filepath=file_path)[0]
        seed = self.config.get_int("seed")
        animate = self.config.get_bool('animate', False)

        if animate:
            try:
                np.random.seed(seed)
                self.modeler = MeshModeler(self.obj.data, 8)
                self.modeler.segment_mesh()
                self.modeler.build_skeleton()
                self.modeler.build_animation(n_frames)
                bpy.app.handlers.frame_change_pre.append(self.mesh_deform_handler)
            except Exception as e:
                print('Mesh segmentation failed. Bailing!', e)
                raise e

        self.name = self.obj.name
        self.obj.scale = self.config.get_vector('scale')

        pts = [i/(n_frames-1) for i in range(n_frames)]
        locations_np = poly.polyval(pts, self.location_poly)
        rotations_np = poly.polyval(pts, self.rotation_poly)

        locations = locations_np.transpose(1, 0).astype(float).tolist()
        rotations = rotations_np.transpose(1, 0).astype(float).tolist()

        for i in range(n_frames):
            self.obj.location = Vector(locations[i])
            self.obj.rotation_euler = Euler(rotations[i])

            self.obj.keyframe_insert(data_path='location', frame=i)
            self.obj.keyframe_insert(data_path='rotation_euler', frame=i)
