from src.main.Module import Module
from src.utility.Utility import Utility
from src.utility.BlenderUtility import get_all_mesh_objects

import bpy

class CameraObjectTrajRunner(Module):
    """ Run an complete predefined trajectory

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "n_frames", "Total number of frames"
       "object_runner", "object.ObjectTrajectoryRunner"
       "camera_runner", "camera.CameraTrajectoryRunner"
    """

    def __init__(self, config):
        Module.__init__(self, config)

        object_runner_config = config.get_raw_dict("object_runner", {})
        camera_runner_config = config.get_raw_dict("camera_runner", {})

        self._object_runner = Utility.initialize_modules([object_runner_config], {})[0]
        self._camera_runner = Utility.initialize_modules([camera_runner_config], {})[0]
    
    def run(self):
        n_frames = self.config.get_int("n_frames", -1)

        self._camera_runner.run(n_frames)
        self._object_runner.run(n_frames)

        bpy.context.scene.frame_end += n_frames
        bpy.context.view_layer.update()
