from src.camera.CameraModule import CameraModule
from src.utility.BlenderUtility import get_all_mesh_objects
from src.utility.Config import Config
import mathutils
import bpy
import bmesh
import sys
import numbers
from collections import defaultdict

class CameraTrajectoryRunner(CameraModule):
    """ Run the camera along the predefined trajectory with no valid pose checking
    """

    def __init__(self, config):
        CameraModule.__init__(self, config)
        self.locations = config.get_list("cam_poses/locations")
        self.look_at = config.get_list("cam_poses/look_at")
        self.intri_config = Config(config.get_raw_dict('intrinsics'))

    def run(self, n_frames):
        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data

        # Use the same intrinsics
        self._set_cam_intrinsics(cam, self.intri_config)

        for i in range(n_frames):

            # Resolve a new camera pose, sets the parameters of the given camera object accordingly.
            location = self.locations[i]
            look_at = self.look_at[i]
            cam_ob.matrix_world = self._cam2world_matrix_from_cam_extrinsics_look_at(location, look_at)

            self._insert_key_frames(cam, cam_ob, i)