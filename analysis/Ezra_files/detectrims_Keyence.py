import os
import cv2
import numpy as np
import tifffile as tiff
from scipy.spatial import KDTree
import pandas as pd


def detectrims_Keyence(path, debug_path,outerthresh,innerthresh,dynamic_mode,debug_mode,skip,max_rim_match_distance = 5):
    # Output dicts
    overlaps_dict = {}
    all_myelin_dict = {}
    debug_output = []


    # Function to find centers of objects
    def get_centroid(contour):
        coords = contour.reshape(-1, 2)
        return tuple(np.mean(coords, axis=0))


    # Loop through wells and fovs
    for well in sorted(os.listdir(path)):
        well_path = os.path.join(path, well)
        if os.path.isdir(well_path):
            for fov in sorted(os.listdir(well_path)):
                fov_path = os.path.join(well_path, fov)
                if os.path.isdir(fov_path):
                    print(fov)

                    if debug_mode:
                        debug_fov = []
                        debug_outer_rims = []
                        debug_inner_rims = []
                        debug_outer_and = []
                        debug_inner_and = []
                        # Create the directory if it doesn't exist
                        debug_dir = os.path.join(fov_path,"DEBUG")
                        os.makedirs(debug_dir, exist_ok=True)

                    # Initiate pillar_groups which is a list of dicts that collects slices for each pillar
                    pillar_groups = []
                    pillar_group_centroids = []

                    # Load full z-stacks
                    pillars = tiff.imread(os.path.join(fov_path, "MASKS/mask-pillars.tif"))
                    i_myelins = tiff.imread(os.path.join(fov_path, f"MASKS/mask-myelin-raw-8000.tif"))
                    o_myelins = tiff.imread(os.path.join(fov_path, f"MASKS/mask-myelin-stack-{outerthresh}.tif"))


                    kernel = np.ones((3, 3), np.uint8)  # 3x3 square structuring element

                    if skip:
                        zrange = [z for z in range(pillars.shape[0]) if z not in skip]
                    else:
                        zrange = range(pillars.shape[0])
                    
                    # Loop through each z slice
                    for zcount,z in enumerate(zrange):
                        # Specify the slice being looked at
                        i_myelin = i_myelins[z]
                        o_myelin = o_myelins[z]
                        pillar = pillars[z]
                        

                        # Initiate px counting bins
                        myelin = 0
                        myelin50_u = 0
                        myelin50_c = 0
                        myelin80_u = 0
                        myelin80_c = 0

                        dilated1 = cv2.dilate(pillar, kernel, iterations=1)
                        dilated2 = cv2.dilate(pillar, kernel, iterations=2)

                        # Define outlines for each inner and outer rim
                        i_contours, _ = cv2.findContours(dilated1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)


                        if dynamic_mode:
                            # Dynamic max rim distance based on axon diameter
                            xcontours = [contour[:,0,0] for contour in i_contours]
                            max_rim_match_distance = 0.5 * np.average([(max(contour) - min(contour)) for contour in xcontours])

                        # Define outlines for each inner and outer rim
                        o_contours, _ = cv2.findContours(dilated2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

                        if debug_mode:
                            debug_zero_mask = np.zeros_like(pillar)
                            debug_outer = cv2.drawContours(debug_zero_mask.copy(), o_contours, -1, 255, thickness=1)
                            debug_inner = cv2.drawContours(debug_zero_mask.copy(), i_contours, -1, 255, thickness=1)

                            debug_outer_rims.append(debug_outer)
                            debug_inner_rims.append(debug_inner)

                            # Compute myelin overlaps
                            debug_outer_and.append(cv2.bitwise_and(debug_outer, o_myelin))
                            debug_inner_and.append(cv2.bitwise_and(debug_inner, i_myelin))
            

                        # Define centers for each outline for each inner and outer rim
                        inner_centroids = [get_centroid(c) for c in i_contours]
                        outer_centroids = [get_centroid(c) for c in o_contours]

                        # kdtree_a stores the inner centers
                        kdtree_a = KDTree(inner_centroids)

                        # This does a search for every outer center to find the closest inner center
                        dists_a, idxs = kdtree_a.query(outer_centroids, distance_upper_bound=max_rim_match_distance)
                        
                        # Create masks
                        inner_mask = np.zeros_like(pillar, dtype=np.uint8)
                        outer_mask = np.zeros_like(pillar, dtype=np.uint8)

                        # Loop through each outer center
                        for i, outer_c in enumerate(outer_centroids):
                            # Checks that there is a match within the max distance
                            if np.isfinite(dists_a[i]):
                                idx = idxs[i]

                                # Reset masks
                                inner_mask.fill(0)
                                outer_mask.fill(0)

                                # Define inner and outer contours
                                inner = i_contours[idx]
                                outer = o_contours[i]


                                # Draw and fill the outer contour
                                cv2.drawContours(inner_mask, inner, -1, 255, thickness=1)

                                # Draw and fill the outer contour
                                cv2.drawContours(outer_mask, outer, -1, 255, thickness=1)


                                # Compute myelin overlaps
                                inner_and = cv2.bitwise_and(inner_mask, i_myelin)
                                outer_and = cv2.bitwise_and(outer_mask, o_myelin)


                                # Find pct overlap
                                percent_wrap_inner = np.count_nonzero(inner_and) / np.count_nonzero(inner_mask)
                                percent_wrap_outer = np.count_nonzero(outer_and) / np.count_nonzero(outer_mask)

                                # Match to existing group by looping through pillars and comparing centers
                                matched = False
                                # If this isnt the first time matching
                                if pillar_group_centroids:
                                    # Query KDTree for nearest centroid
                                    dist_b, idx = kdtree_b.query(outer_c, distance_upper_bound=max_rim_match_distance)
                                    # Checks that there is a match within the max distance
                                    if np.isfinite(dist_b):
                                        group = pillar_groups[idx]
                                        group['data'].append((zcount, percent_wrap_inner, percent_wrap_outer))
                                        group['myelin_px'] += np.count_nonzero(inner_and)
                                        matched = True

                                # If not matched, add new group and rebuild KDTree
                                if not matched:
                                    pillar_groups.append({
                                        'centroid': outer_c,
                                        'data': [(zcount, percent_wrap_inner, percent_wrap_outer)],
                                        'myelin_px': np.count_nonzero(inner_and)
                                    })
                                    pillar_group_centroids.append(outer_c)
                                    # Need to rebuild kdtree_b every time a new pillar is created
                                    kdtree_b = KDTree(pillar_group_centroids)

                    if debug_mode:
                        # Save as a TIFF stack
                        debug_outer_rims_stack = np.stack(debug_outer_rims)
                        debug_inner_rims_stack = np.stack(debug_inner_rims)
                        debug_outer_and_stack = np.stack(debug_outer_and)
                        debug_inner_and_stack = np.stack(debug_inner_and)

                        o_rim_path = os.path.join(debug_dir,"outer_rims.tif")
                        i_rim_path = os.path.join(debug_dir,"inner_rims.tif")
                        o_and_path = os.path.join(debug_dir,"outer_overlap.tif")
                        i_and_path = os.path.join(debug_dir,"inner_overlap.tif")

                        tiff.imwrite(o_rim_path, debug_outer_rims_stack)
                        tiff.imwrite(i_rim_path, debug_inner_rims_stack)
                        tiff.imwrite(o_and_path,debug_outer_and_stack)
                        tiff.imwrite(i_and_path,debug_inner_and_stack)

                    # Add to myelin counts when threshold is met
                    for group in pillar_groups:
                        data = group['data']
                        px = group['myelin_px']
                        if any(pct >= 0.5 for _, pct, _ in data):
                            myelin50_u += px
                        if any(((inner >= 0.5) and not ((outer >= 0.95) and (inner >= 0.9))) for _, inner, outer in data):
                            myelin50_c += px
                        if any(pct >= 0.8 for _, pct, _ in data):
                            myelin80_u += px
                        if any(((inner >= 0.8) and not ((outer >= 0.95) and (inner >= 0.9))) for _, inner, outer in data):
                            myelin80_c += px
                        myelin += px


                    # Build final simplified output (by pillar index)
                    overlap = []
                    for pillar_idx, group in enumerate(pillar_groups):
                        for z, inner_pct, outer_pct in group['data']:
                            center = group['centroid'] # x,y
                            overlap.append([pillar_idx, center, z, inner_pct, outer_pct])
                            if debug_mode:
                                center_x, center_y = map(int, outer_c)
                                debug_fov.append({"fov": fov,
                                                  "id": pillar_idx,
                                                    "X": center_x,
                                                    "Y": center_y,
                                                    "Z": z,
                                                    "Pct_Wrap_i": inner_pct,
                                                    "Pct_Wrap_o": outer_pct})


                    # Dicts are filled by well,fov
                    overlaps_dict[(well, fov)] = overlap
                    all_myelin_dict[(well, fov)] = [myelin, myelin50_u,myelin50_c, myelin80_u,myelin80_c]

                    if debug_mode:
                        debug_fov = sorted(debug_fov, key=lambda x:(x['X'],x['Y'],x['Z']))
                        debug_output.append(debug_fov)


    if debug_mode:
        flat_debug_output = [row for fov in debug_output for row in fov]

        pros_wrap_data = pd.DataFrame(flat_debug_output, columns=["fov","id","X", "Y", "Z","Pct_Wrap_i","Pct_Wrap_o"])
        pros_wrap_data.to_csv(debug_path, index=False)

    return overlaps_dict, all_myelin_dict