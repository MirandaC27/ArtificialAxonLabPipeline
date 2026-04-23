import pandas as pd
import os


def detectnuclei(set_path):
    nuclei_dict = {}  # key: (well, fov), value: number of nuclei (contours)

    # Define allowed wells: B02–B11
    allowed_wells = {f"B{str(i).zfill(2)}" for i in range(2, 12)}

    for well in sorted(os.listdir(set_path)):
        if well not in allowed_wells:
            continue

        well_path = os.path.join(set_path, well)
        if os.path.isdir(well_path):
            for fov in sorted(os.listdir(well_path)):
                fov_path = os.path.join(well_path, fov)
                if os.path.isdir(fov_path):

                    nuclei_path = os.path.join(fov_path, "DATA", "nuclei.out")
                    df = pd.read_csv(nuclei_path, sep="\t")

                    # Store count
                    nuclei_dict[(well, fov)] = df.loc[0, "Count"]

    return nuclei_dict