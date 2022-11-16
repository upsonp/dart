from django import forms

from core import models


class MissionSettingsForm(forms.ModelForm):

    # elog_dir = forms.CharField(max_length=255, label="Elog Directory", required=True,
    #                            help_text="Folder location of Elog *.log files")
    # bottle_dir = forms.CharField(max_length=255, label="CTD Bottle Directory", required=True,
    #                              help_text="Folder location of Elog *.BTL files")

    class Meta:
        model = models.Mission
        fields = ["name"]  # , "elog_dir", "bottle_dir"]