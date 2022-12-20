import os
from os.path import join

from django.http import JsonResponse

from core import validations
from core import models
from core.parsers import elog
from core.parsers import ctd
from core.parsers import salt
from core.parsers import oxygen
from core.parsers import chl


def get_files(request):
    type = models.FileType[request.GET['file_type'].lower()] if 'file_type' in request.GET else None
    mission = request.GET['mission_id'] if 'mission_id' in request.GET else None

    files = []
    t_log_dir = models.DataFileDirectory.objects.filter(mission_id=mission, file_types__file_type=type.value)
    if t_log_dir:
        log_dir = t_log_dir[0]
    else:
        return JsonResponse({'files': []})

    for path in os.listdir(log_dir.directory):
        if os.path.isfile(join(log_dir.directory, path)) and path.lower().endswith(type.label.lower()):
            if len(log_dir.data_files.filter(file=path)) <= 0:
                files.append(models.DataFile(directory=log_dir, file_type=type.value, file=path, processed=False))

    models.DataFile.objects.bulk_create(files)

    resp = JsonResponse({'files': [{'fid': f.pk, 'file_name': f.file.name, 'processed': f.processed,
                                    'errors': len(models.Error.objects.filter(file=f)) > 0} for f in
                                   models.DataFile.objects.filter(directory=log_dir)]})

    return resp


def get_ctd_files(request):
    btl_files = []
    mission_id = request.GET['mission_id']
    if 'fid' in request.GET:

        fid = request.GET["fid"]

        btl_dir = models.DataFileDirectory.objects.get(mission_id=mission_id,
                                                       file_types__file_type=models.FileType.btl.value)
        btl_file = btl_dir.data_files.get(pk=fid)
        btl_file.log_errors.all().delete()

        ctd.read_ctd(btl_file)
        btl_files.append(btl_file)

        errors = models.Error.objects.filter(file=btl_file)
        if len(errors) > 0:
            return JsonResponse({'errors': [{"pk": e.pk, "line": e.line, "msg": e.message, "trace": e.stack_trace}
                                            for e in errors]})
        else:
            btl_file.processed = True
            btl_file.save()

    return JsonResponse({'action': 'updated'})


def process_elog(request):
    mission_id = request.GET['mission_id']
    if 'fid' in request.GET:

        fid = request.GET["fid"]

        log_dir = models.DataFileDirectory.objects.get(mission_id=mission_id,
                                                       file_types__file_type=models.FileType.log.value)
        log_file = log_dir.data_files.get(pk=fid)
        log_file.log_errors.all().delete()

        elog.read_elog(log_file)

        validations.validate_events(log_file)

        errors = models.Error.objects.filter(file=log_file)
        if len(errors) > 0:
            return JsonResponse({'errors': [{"pk": e.pk, "line": e.line, "msg": e.message, "trace": e.stack_trace}
                                            for e in errors]})
        else:
            log_file.processed = True
            log_file.save()

    return JsonResponse({'action': 'updated'})


def process_ctd(request, mission_id):
    ctd_files = []
    updated = []
    ctd_file = None
    if 'fid' in request.GET:
        fid = request.GET["fid"]

        ctd_file = models.DataFile.objects.get(pk=fid, file_type=models.FileType.btl.value)

        try:
            ctd.read_ctd(ctd_file)
            ctd_files.append(ctd_file)

            post_ctd_validation(ctd_files)
            ctd_file.processed = True
            ctd_file.save()

            updated.append(fid)
        except models.Event.DoesNotExist as e:
            err = models.Error(mission_id=mission_id, file=ctd_file, line=-1, message=f"Error Processing file",
                               stack_trace=str(e))
            err.save()

    elif 'did' in request.GET:
        did = request.GET["did"]

        post_ctd_validation(ctd_files)

    errors = models.Error.objects.filter(file=ctd_file)
    return JsonResponse({'updated': updated, "errors": [{"pk": e.pk, "line": e.line, "msg": e.message,
                                                         "trace": e.stack_trace} for e in errors]})



def post_ctd_validation(ctd_files):
    pass


def load_samples(request, pk):
    errors = []
    file_type = request.GET['type']
    files = request.FILES

    file_names = files.keys()
    for fname in file_names:
        models.Error.objects.filter(file_name=fname).delete()

        print(f"Load Start: {fname}")
        if file_type == 'salt':
            errors += salt.load_salt(pk, files[fname])
        elif file_type == 'oxy':
            errors += oxygen.load_oxy(pk, files[fname])
        elif file_type == 'chl':
            errors += chl.load_chl(pk, files[fname])
        print(f"Load Finished")

    return JsonResponse({"errors": [{"pk": e.pk, "msg": e.message, "trace": e.stack_trace} for e in errors]})
