import pandas as pd
import os
from itertools import groupby

def analysis(path,out_path,further_analysis_path,overlaps_dict,nuclei_dict,areas_dict,myelin_dict, skip, further_analysis_mode):
    

    total_pillars = []        # total number of pillars
    wrap_any_pillars = []     # total number of pillars with at least one pixel of myelin around it
    wrap_50_pillars_u = []      # total number of pillars with at least one z stack that is >50% wrapped
    wrap_50_pillars_c = []      # total number of pillars with at least one z stack that is >50% wrapped
    wrap_80_pillars_u = []      # total number of pillars with at least one z stack that is >80% wrapped
    wrap_80_pillars_c = []      # total number of pillars with at least one z stack that is >80% wrapped
    wrap_80_three_stack_u = []  # total number of pillars with at least three z stack that is >80% wrapped
    wrap_80_three_stack_c = []  # total number of pillars with at least three z stack that is >80% wrapped
    wrap_80_five_stack_u = []   # total number of pillars with at least five z stack that is >80% wrapped
    wrap_80_five_stack_c = []   # total number of pillars with at least five z stack that is >80% wrapped
    wrap_any_myelin = []      # total area of myelin present
    wrap_50_myelin_u = []       # total area of myelin around all pillars that are >50% wrapped (Uncondensed)
    wrap_50_myelin_c = []       # total area of myelin around all pillars that are >50% wrapped (Condensed)
    wrap_80_myelin_u = []     # total area of myelin around all pillars that are >80% wrapped (Includes uncondense)
    wrap_80_myelin_c = []     # total area of myelin around all pillars that are >80% wrapped (Doesn't includes uncondense)
    average_full_wrapping_length_u = []   # of the pillars that contain full wrapping, the average length of full wrapping (in microns)
    average_full_wrapping_length_c = []   # of the pillars that contain full wrapping, the average length of full wrapping (in microns)
    well_array = []           # Track wells
    fov_array = []            # Track fov
    z_projection = []         # z projected myelin
    total_nuclei = []         # Total nuclei in fov
    index_u = []                # Index of fov
    index_c = []                # Index of fov
    further_output = []       # Store for further analysis

    for well in sorted(os.listdir(path)):
        well_path = os.path.join(path, well)
        if os.path.isdir(well_path):
            for fov in sorted(os.listdir(well_path)):
                fov_path = os.path.join(well_path, fov)
                if os.path.isdir(fov_path):


                    # Append from dicts
                    well_array.append(well)
                    fov_array.append(fov)
                    z_projection.append(areas_dict[(well,fov)])
                    total_nuclei.append(nuclei_dict[(well,fov)])
                    wrap_any_myelin.append(myelin_dict[(well,fov)][0])
                    wrap_50_myelin_u.append(myelin_dict[(well,fov)][1])
                    wrap_50_myelin_c.append(myelin_dict[(well,fov)][2])
                    wrap_80_myelin_u.append(myelin_dict[(well,fov)][3])
                    wrap_80_myelin_c.append(myelin_dict[(well,fov)][4])
                    overlap = overlaps_dict[(well,fov)] # {well,fov}:[id,outer_center,z,inner_pct,outer_pct]
                    
                    unique_pillars = set(pillar[0] for pillar in overlap)
                    total_pillars.append(len(unique_pillars))

                    # Initialize counts
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
                        pillar_data = [row for row in overlap if row[0] == pillar]  # [id,outer_center(x,y),z,inner_pct,outer_pct]
                        
                        # Get all overlaps for this pillar sorted
                        # slice[4] is outer overlap and slice[3] is inner overlap

                        pillar_50_u = sorted([slice[2] for slice in pillar_data if (slice[3] >= 0.5)])
                        pillar_80_u = sorted([slice[2] for slice in pillar_data if (slice[3] >= 0.8)])

                        pillar_50_c = sorted([slice[2] for slice in pillar_data if (slice[3] >= 0.5) and not ((slice[4] >= 0.95) & (slice[3] >= 0.9))])
                        pillar_80_c = sorted([slice[2] for slice in pillar_data if (slice[3] >= 0.8) and not ((slice[4] >= 0.95) & (slice[3] >= 0.9))])

                        # If there is any wraping in the pillar add to wrap_any_p
                        if any(row[3] > 0 for row in pillar_data):
                            wrap_any_p += 1

                        # Find max runs
                        if pillar_50_u:
                            runs50_u = max([len(list(g)) for _, g in groupby(enumerate(pillar_50_u), lambda ix: ix[0] - ix[1])])
                        else:
                            runs50_u = 0
                        if pillar_80_u:
                            runs80_u = max([len(list(g)) for _, g in groupby(enumerate(pillar_80_u), lambda ix: ix[0] - ix[1])])
                        else:
                            runs80_u = 0
                        # Add to wrap counts
                        if runs50_u > 0:
                            wrap_50_u += 1
                        if runs80_u > 0:
                            wrap_80_u += 1
                            full_wrap_len_u += runs80_u * 2 # 2 microns a z slice NEED TO CHANGE DEPENDING ON skip
                        if skip: # NEED TO CHANGE DEPENDING ON skip
                            if runs80_u > 1:
                                wrap_80_3_u += 1
                            if runs80_u > 2:
                                wrap_80_5 += 1
                        else:
                            if runs80_u > 2:
                                wrap_80_3_u += 1
                            if runs80_u > 4:
                                wrap_80_5_u += 1

                        # Find max runs
                        if pillar_50_c:
                            runs50_c = max([len(list(g)) for _, g in groupby(enumerate(pillar_50_c), lambda ix: ix[0] - ix[1])])
                        else:
                            runs50_c = 0
                        if pillar_80_c:
                            runs80_c = max([len(list(g)) for _, g in groupby(enumerate(pillar_80_c), lambda ix: ix[0] - ix[1])])
                        else:
                            runs80_c = 0
                        # Add to wrap counts
                        if runs50_c > 0:
                            wrap_50_c += 1
                        if runs80_c > 0:
                            wrap_80_c += 1
                            full_wrap_len_c += runs80_c * 2 # 2 microns a z slice NEED TO CHANGE DEPENDING ON skip
                        if skip: # NEED TO CHANGE DEPENDING ON skip
                            if runs80_c > 1:
                                wrap_80_3_c += 1
                            if runs80_c > 2:
                                wrap_80_5_c += 1
                        else:
                            if runs80_c > 2:
                                wrap_80_3_c += 1
                                pillar_c = pillar_data[0][1] # All centers are written as the first one in the stack
                                further_output.append({'fov':fov,'X':pillar_c[0],'Y':pillar_c[1]})
                            if runs80_c > 4:
                                wrap_80_5_c += 1
                    
                    # Append to counts
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
                    index_u.append(wrap_80_3_u / nuclei_dict[(well,fov)])
                    index_c.append(wrap_80_3_c / nuclei_dict[(well,fov)])

    if further_analysis_mode:
        further_df = pd.DataFrame(further_output)
        further_df.to_csv(further_analysis_path, index=False)

    # Gather all the data into a dataframe
    processed_data = {'well': well_array, 
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
                'Index_c': index_c}


    processed_df = pd.DataFrame(processed_data)  

    processed_df.to_csv(out_path)