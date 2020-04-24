import bpy

from src.utility.BlenderUtility import get_mesh_objects_with_name
from src.main.Module import Module
from src.utility.Utility import Utility
from src.object.MeshDeformer import MeshModeler

from mathutils import Vector, Euler
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
        self.locations = self.config.get_list("poses/locations")
        self.rotations = self.config.get_list("poses/rotations")

    # I have no idea why it gives me 3 arguments
    # Maybe it just wants to argue with me
    def mesh_deform_handler(self, scene, sth):
        frame = scene.frame_current

        if frame == 0:
            self.obj = get_mesh_objects_with_name([self.name])[0]
            self.modeler.mesh = self.obj.data

        self.modeler.mod_rotation(frame)
        self.modeler.apply_transformation()

    def run(self, n_frames):

        file_path = Utility.resolve_path(self.config.get_string("path"))
        self.obj = Utility.import_objects(filepath=file_path)[0]
        self.modeler = MeshModeler(self.obj.data, 8)
        self.modeler.segment_mesh()
        self.modeler.build_skeleton()

        self.name = self.obj.name
        self.obj.scale = self.config.get_vector('scale')

        bpy.app.handlers.frame_change_pre.append(self.mesh_deform_handler)

        # objects = get_mesh_objects_with_name(self.config.get_list('target_names'))

        for i in range(n_frames):
            self.obj.location = Vector(self.locations[i])
            self.obj.rotation_euler = Euler(self.rotations[i])

            self.obj.keyframe_insert(data_path='location', frame=i)
            self.obj.keyframe_insert(data_path='rotation_euler', frame=i)
