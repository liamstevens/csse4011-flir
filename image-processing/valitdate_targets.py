import target from target_lib

# This function requires targets and rois to be sorted properly
# Returns sorted list to 
def validate_targets(targets, rois):

    out = []

    # Iterate through all targets (check for for valid rois, put them in)
    for item in targets:
        for roi in rois:
            roi_not_found = True
            
            # Pop from list if roi is valid
            if item.validate_roi(roi):
                out.add(rois.pop(roi))
                roi_not_found = False
                break

        # If no valid rois found, just add empty element
        if roi_not_found:
            out.add(None)

    return out