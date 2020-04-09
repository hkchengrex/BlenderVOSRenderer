from src.main.Module import Module
from src.utility.Utility import Utility
from src.utility.BlenderUtility import get_all_mesh_objects

import bpy

class VOSTrajRunner(Module):
    """ Run an complete predefined trajectory

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "n_frames", "Total number of frames"
       "object_runner", "object.ObjectTrajectoryRunner"
       "camera_runner", "camera.CameraTrajectoryRunner"
       "light_runner", "light.LightTrajectoryRunner"
    """

    def __init__(self, config):
        Module.__init__(self, config)

        camera_runner_config = config.get_raw_dict("camera_runner", {})

        object_runners_config = config.get_list("object_runners", [])
        light_runners_config = config.get_list("light_runners", [])

        self._camera_runner = Utility.initialize_modules([camera_runner_config], {})[0]
        self._object_runners = Utility.initialize_modules(object_runners_config, {})
        self._light_runners = Utility.initialize_modules(light_runners_config, {})
    
    def run(self):
        n_frames = self.config.get_int("n_frames", -1)

        self._camera_runner.run(n_frames)

        for runner in self._object_runners:
            runner.run(n_frames)
        for runner in self._light_runners:
            runner.run(n_frames)

        bpy.context.scene.frame_end += n_frames
        bpy.context.view_layer.update()
