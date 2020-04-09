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

    .. csv-table::
       :header: "Parameter", "Description"

       "target_name", "Name of the object to be controlled."
       "poses", "Poses to be used in each time frame."
    """

    def __init__(self, config):
        CameraModule.__init__(self, config)
        self.cam_poses = self.config.get_list("cam_poses")

    def run(self, n_frames):
        cam_ob = bpy.context.scene.camera
        cam = cam_ob.data

        for i in range(n_frames):
            config = Config(self.cam_poses[i])

            self._set_cam_intrinsics(cam, config)
            cam_ob.matrix_world = self._cam2world_matrix_from_cam_extrinsics(config)

            self._insert_key_frames(cam, cam_ob, i)

    def resolve_cam_pose(self, cam, cam_ob, config):
        """ Resolve a new camera pose, sets the parameters of the given camera object accordingly.

        :param cam: The camera which contains only camera specific attributes.
        :param cam_ob: The object linked to the camera which determines general properties like location/orientation
        :param config: The config object describing how to sample
        """
        # Sample/set camera intrinsics
        self._set_cam_intrinsics(cam, config)

        # Sample camera extrinsics (we do not set them yet for performance reasons)
        cam_ob.matrix_world = self._cam2world_matrix_from_cam_extrinsics(config)