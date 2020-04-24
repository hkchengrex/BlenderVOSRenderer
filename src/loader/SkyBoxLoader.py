import bpy

from src.loader.Loader import Loader
from src.utility.Utility import Utility


class SkyBoxLoader(Loader):
    """ Just imports the objects for the given file path & scale

    The import will load all materials into cycle nodes.

    **Configuration**:

    .. csv-table::
       :header: "Parameter", "Description"

       "path", "The path to the 3D data file to load. Can be either path or paths not both."
    """
    def __init__(self, config):
        Loader.__init__(self, config)

    def run(self):

        file_path = Utility.resolve_path(self.config.get_string("path"))
        loaded_object = Utility.import_objects(filepath=file_path)[0]
        loaded_object.scale = self.config.get_vector("scale")