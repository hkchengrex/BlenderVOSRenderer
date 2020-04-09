import bpy

from src.utility.BlenderUtility import get_mesh_objects_with_name
from src.main.Module import Module
from src.utility.Utility import Utility

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

    def run(self, n_frames):

        file_path = Utility.resolve_path(self.config.get_string("path"))
        obj = Utility.import_objects(filepath=file_path)[0]
        obj.scale = self.config.get_vector('scale')

        # objects = get_mesh_objects_with_name(self.config.get_list('target_names'))

        for i in range(n_frames):
            obj.location = Vector(self.locations[i])
            obj.rotation_euler = Euler(self.rotations[i])

            obj.keyframe_insert(data_path='location', frame=i)
            obj.keyframe_insert(data_path='rotation_euler', frame=i)
