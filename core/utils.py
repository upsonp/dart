from django.http import JsonResponse

from core import models


def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False


def isint(num):
    try:
        int(num)
        return True
    except ValueError:
        return False


def convertDMS_degs(dms_string):
    dms = dms_string.split()
    nsew = dms[2].upper()  # north, south, east, west
    degs = (float(dms[0]) + float(dms[1]) / 60) * (-1 if (nsew == 'S' or nsew == 'W') else 1)

    return degs


def convertDegs_DMS(dd):
    d = int(dd)
    m = float((dd - d) * 60.0)

    return [d, m]


def ajax_set_directory(request, mission):
    dir = request.GET['dir']
    f_type = request.GET['type']

    return set_directory(mission_id=mission, directory=dir, file_type=f_type)


def set_directory(mission_id, directory, file_type):
    mission = models.Mission.objects.get(pk=mission_id)

    data_dir = mission.mission_directories.filter(file_types__file_type=models.FileType[file_type].value)

    if len(data_dir) > 0:
        data_dir[0].directory = directory
        data_dir[0].save()

        return JsonResponse({})

    dfd = models.DataFileDirectory(mission=mission, directory=directory)
    dfd.save()

    dfd_type = models.DataFileDirectoryType(directory=dfd, file_type=models.FileType[file_type].value)
    dfd_type.save()

    return JsonResponse({})
