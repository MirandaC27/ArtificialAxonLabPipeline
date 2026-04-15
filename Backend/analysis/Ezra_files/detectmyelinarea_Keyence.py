import os
import numpy as np
import tifffile as tiff


def detectmyelinarea_Keyence(path,narrowthresh,debug_mode):
    myelin_area_dict = {}
    for well in sorted(os.listdir(path)):
        well_path = os.path.join(path, well)
        if os.path.isdir(well_path):
            for fov in sorted(os.listdir(well_path)):
                fov_path = os.path.join(well_path, fov)
                if os.path.isdir(fov_path):
                    # Read myelin mask
                    n_myelins = tiff.imread(os.path.join(fov_path, f"MASKS/mask-myelin-stack-{narrowthresh}.tif")) 
                    # Z-projection (maximum intensity)
                    n_myelins_proj = np.max(n_myelins, axis=0)

                    if debug_mode:
                        debug_dir = os.path.join(fov_path,"DEBUG")
                        debug_zpro = n_myelins_proj
                        debug_zpro_path = os.path.join(debug_dir,"zpro.tif")
                        tiff.imwrite(debug_zpro_path, debug_zpro)

                    # Calculate area (number of nonzero pixels)
                    area = np.count_nonzero(n_myelins_proj)

                    myelin_area_dict[(well,fov)] = area
    return myelin_area_dict
