import subprocess as sp


def call_subprocess(action, function_name, logger=None):
    """Call a subprocess action

    Args:
        action (str): string to run
        function_name (str): function name for Exception
        logger (logger, optional): Log information to the logger if provided.
            Defaults to None.

    Raises:
        Exception: If gdalwarp fails

    Returns:
        boolean: True if gdalwarp successful
    """

    with sp.Popen(
        action,
        shell=True,
        stdout=sp.PIPE,
        stderr=sp.PIPE,
        universal_newlines=True
    ) as s:

        output = []
        for line in iter(s.stdout.readline, ""):
            if logger is not None:
                logger.debug(line.rstrip())
            output.append(line.rstrip())

        # if errors then create an exception
        return_code = s.wait()
        if return_code:
            if logger is not None:
                for line in output:
                    logger.error(line)
            raise Exception('{} has an error'.format(function_name))

        return True


def gdalwarp(src_image, dst_image, target_crs, extents,
             cell_size, resample='bilinear', logger=None):
    """gdalwarp to reproject, resample cell size and crop to extent

    Args:
        src_image (str): source DEM file
        dst_image (str): destination file for reprojected file
        target_crs (str): EPSG code, i.e. EPSG:32611
        extents (list): Extents to crop to [left, bottom, right, top]
        cell_size (float): cell size to resample to
        resample (str, optional): resampling method. Defaults to 'bilinear'.
        logger (logging, optional): Log information to the logger if provided.
            Defaults to None.

    Returns:
        boolean: True if call to gdalwarp was successful
    """

    cmd = "gdalwarp -t_srs {} -te {}, {}, {}, {} -tr {} {} -r {} -overwrite {} {}".format(  # noqa
        target_crs,
        extents[0],
        extents[1],
        extents[2],
        extents[3],
        cell_size,
        cell_size,
        resample,
        src_image,
        dst_image
    )

    if logger is not None:
        logger.debug(cmd)

    return call_subprocess(cmd, 'gdalwarp', logger)
