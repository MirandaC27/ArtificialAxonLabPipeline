import pandas as pd
import os
from itertools import groupby


def analysis(path, out_path, further_analysis_path,
             overlaps_dict, nuclei_dict, areas_dict, myelin_dict,
             skip, further_analysis_mode):

    # -----------------------------
    # Restrict to wells B02–B11
    # -----------------------------
    allowed_wells = {f"B{str(i).zfill(2)}" for i in range(2, 12)}

    total_pillars = []
    wrap_any_pillars = []
    wrap_50_pillars_u = []
    wrap_50_pillars_c = []
    wrap_80_pillars_u = []
    wrap_80_pillars_c = []
    wrap_80_three_stack_u = []
    wrap_80_three_stack_c = []
    wrap_80_five_stack_u = []
    wrap_80_five_stack_c = []
    wrap_any_myelin = []
    wrap_50_myelin_u = []
    wrap_50_myelin_c = []
    wrap_80_myelin_u = []
    wrap_80_myelin_c = []
    average_full_wrapping_length_u = []
    average_full_wrapping_length_c = []
    well_array = []
    fov_array = []
    z_projection = []
    total_nuclei = []
    index_u = []
    index_c = []
    further_output = []

    for well in sorted(os.listdir(path)):

        # -----------------------------
        # FILTER HERE
        # -----------------------------
        if well not in allowed_wells:
            continue

        well_path = os.path.join(path, well)
        if os.path.isdir(well_path):
            for fov in sorted(os.listdir(well_path)):
                fov_path = os.path.join(well_path, fov)
                if os.path.isdir(fov_path):

                    well_array.append(well)
                    fov_array.append(fov)

                    #z_projection.append(areas_dict[(well, fov)])
                    total_nuclei.append(nuclei_dict[(well, fov)])

                    wrap_any_myelin.append(myelin_dict[(well, fov)][0])
                    wrap_50_myelin_u.append(myelin_dict[(well, fov)][1])
                    wrap_50_myelin_c.append(myelin_dict[(well, fov)][2])
                    wrap_80_myelin_u.append(myelin_dict[(well, fov)][3])
                    wrap_80_myelin_c.append(myelin_dict[(well, fov)][4])

                    #overlap = overlaps_dict[(well, fov)]

                    unique_pillars = set(pillar[0] for pillar in overlap)
                    total_pillars.append(len(unique_pillars))

                    wrap_any_p = 0
                    wrap_50_u = 0
                    wrap_50_c = 0
                    wrap_80_u = 0
                    wrap_80_c = 0
                    wrap_80_3_u = 0
                    wrap_80_3_c = 0
                    wrap_80_5_u = 0
                    wrap_80_5_c = 0
                    full_wrap_len_u = 0
                    full_wrap_len_c = 0

                    for pillar in unique_pillars:
                        pillar_data = [row for row in overlap if row[0] == pillar]

                        pillar_50_u = sorted([s[2] for s in pillar_data if s[3] >= 0.5])
                        pillar_80_u = sorted([s[2] for s in pillar_data if s[3] >= 0.8])

                        pillar_50_c = sorted([s[2] for s in pillar_data if (s[3] >= 0.5) and not ((s[4] >= 0.95) & (s[3] >= 0.9))])
                        pillar_80_c = sorted([s[2] for s in pillar_data if (s[3] >= 0.8) and not ((s[4] >= 0.95) & (s[3] >= 0.9))])

                        if any(row[3] > 0 for row in pillar_data):
                            wrap_any_p += 1

                        runs50_u = max([len(list(g)) for _, g in groupby(enumerate(pillar_50_u), lambda ix: ix[0] - ix[1])]) if pillar_50_u else 0
                        runs80_u = max([len(list(g)) for _, g in groupby(enumerate(pillar_80_u), lambda ix: ix[0] - ix[1])]) if pillar_80_u else 0

                        if runs50_u > 0:
                            wrap_50_u += 1
                        if runs80_u > 0:
                            wrap_80_u += 1
                            full_wrap_len_u += runs80_u * 2

                        if skip:
                            if runs80_u > 1:
                                wrap_80_3_u += 1
                            if runs80_u > 2:
                                wrap_80_5_u += 1
                        else:
                            if runs80_u > 2:
                                wrap_80_3_u += 1
                            if runs80_u > 4:
                                wrap_80_5_u += 1

                        runs50_c = max([len(list(g)) for _, g in groupby(enumerate(pillar_50_c), lambda ix: ix[0] - ix[1])]) if pillar_50_c else 0
                        runs80_c = max([len(list(g)) for _, g in groupby(enumerate(pillar_80_c), lambda ix: ix[0] - ix[1])]) if pillar_80_c else 0

                        if runs50_c > 0:
                            wrap_50_c += 1
                        if runs80_c > 0:
                            wrap_80_c += 1
                            full_wrap_len_c += runs80_c * 2

                        if skip:
                            if runs80_c > 1:
                                wrap_80_3_c += 1
                            if runs80_c > 2:
                                wrap_80_5_c += 1
                        else:
                            if runs80_c > 2:
                                wrap_80_3_c += 1
                                pillar_c = pillar_data[0][1]
                                further_output.append({'fov': fov, 'X': pillar_c[0], 'Y': pillar_c[1]})
                            if runs80_c > 4:
                                wrap_80_5_c += 1

                    wrap_any_pillars.append(wrap_any_p)
                    wrap_50_pillars_u.append(wrap_50_u)
                    wrap_50_pillars_c.append(wrap_50_c)
                    wrap_80_pillars_u.append(wrap_80_u)
                    wrap_80_pillars_c.append(wrap_80_c)
                    wrap_80_three_stack_u.append(wrap_80_3_u)
                    wrap_80_three_stack_c.append(wrap_80_3_c)
                    wrap_80_five_stack_u.append(wrap_80_5_u)
                    wrap_80_five_stack_c.append(wrap_80_5_c)

                    average_full_wrapping_length_u.append(full_wrap_len_u / wrap_80_u if wrap_80_u > 0 else 0)
                    average_full_wrapping_length_c.append(full_wrap_len_c / wrap_80_c if wrap_80_c > 0 else 0)

                    index_u.append(wrap_80_3_u / nuclei_dict[(well, fov)])
                    index_c.append(wrap_80_3_c / nuclei_dict[(well, fov)])

    #if further_analysis_mode:
        #pd.DataFrame(further_output).to_csv(further_analysis_path, index=False)

    processed_data = {
        'well': well_array,
        'fov': fov_array,
        'total_pillars': total_pillars,
        'wrap_any_pillars': wrap_any_pillars,
        'wrap_50_pillars_u': wrap_50_pillars_u,
        'wrap_50_pillars_c': wrap_50_pillars_c,
        'wrap_80_pillars_u': wrap_80_pillars_u,
        'wrap_80_pillars_c': wrap_80_pillars_c,
        'wrap_80_pillars_three_stack_u': wrap_80_three_stack_u,
        'wrap_80_pillars_three_stack_c': wrap_80_three_stack_c,
        'wrap_80_pillars_five_stack_u': wrap_80_five_stack_u,
        'wrap_80_pillars_five_stack_c': wrap_80_five_stack_c,
        'wrap_any_myelin': wrap_any_myelin,
        'wrap_50_myelin_u': wrap_50_myelin_u,
        'wrap_50_myelin_c': wrap_50_myelin_c,
        'wrap_80_myelin_u': wrap_80_myelin_u,
        'wrap_80_myelin_c': wrap_80_myelin_c,
        'average_full_wrapping_length_u': average_full_wrapping_length_u,
        'average_full_wrapping_length_c': average_full_wrapping_length_c,
        'z_projection_area': z_projection,
        'total_nuclei': total_nuclei,
        'Index_u': index_u,
        'Index_c': index_c
    }

    pd.DataFrame(processed_data).to_csv(out_path)