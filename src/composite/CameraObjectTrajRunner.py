from src.main.Module import Module
from src.utility.Utility import Utility
from src.utility.BlenderUtility import get_all_mesh_objects

import bpy

class CameraObjectTrajRunner(Module):
    """ Alternates between sampling new cameras using camera.CameraSampler and sampling new object poses using object.ObjectPoseSampler

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "total_noof_cams", "Total number of sampled cameras"
       "noof_cams_per_scene", "Number of sampled cameras after which object poses are re-sampled"
       "object_pose_sampler", "object.ObjectPoseSampler"
       "camera_pose_sampler", "camera.CameraSampler"
    """

    def __init__(self, config):
        Module.__init__(self, config)

        object_pose_sampler_config = config.get_raw_dict("object_pose_sampler", {})
        camera_pose_sampler_config = config.get_raw_dict("camera_pose_sampler", {})

        self._object_pose_sampler = Utility.initialize_modules([object_pose_sampler_config], {})[0]
        self._camera_pose_sampler = Utility.initialize_modules([camera_pose_sampler_config], {})[0]
    
    def run(self):
        total_noof_cams = self.config.get_int("total_noof_cams", -1)

        self._camera_pose_sampler.run(total_noof_cams)
        self._object_pose_sampler.run(total_noof_cams)

        bpy.context.scene.frame_end += total_noof_cams
        bpy.context.view_layer.update()
