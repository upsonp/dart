from bs4 import BeautifulSoup

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Column, Row, Hidden, Field, Layout, HTML
from crispy_forms.utils import render_crispy_form

from django import forms
from django.http import HttpResponse
from django.urls import path, reverse_lazy
from django.utils.translation import gettext as _
from openid.consumer.html_parse import attr_find

from dart.utils import load_svg
from settingsdb import models as settings_models
from core import forms as core_forms


class PlanForm(core_forms.CardForm, forms.ModelForm):
    _station = None

    attribute = forms.ChoiceField(choices=[])
    class Meta:
        model = settings_models.GlobalStationPlan
        fields = '__all__'

    def get_card_body(self) -> Div:
        attrs = {'hx-trigger': 'update_station_plan from:body', 'hx-get': 'settingsdb:form_station_selected'}
        body = super().get_card_body(**attrs)
        icon = load_svg('check-square')

        pressure_attrs = {
            'hx-post': reverse_lazy('settingsdb:add_pressure')
        }

        submit_pressure = StrictButton(icon, css_class='btn btn-success btn-sm', **pressure_attrs)

        attributes_attrs = {
            'hx-post': reverse_lazy('settingsdb:add_attribute')
        }
        submit_attributes = StrictButton(icon, css_class='btn btn-success btn-sm', **attributes_attrs)

        pressures = settings_models.GlobalStationPlan.objects.filter(station=self.initial['station'])
        global_attrs = settings_models.GlobalSampleTypeCategory.objects.filter(
            attributes__plan__station=self.initial['station']
        ).distinct()

        table = '<table class="table">'
        table += '<thead><tr>'
        table += f'<th>{_("Pressure (m)")}</th>'
        for g_attr in global_attrs:
            table += f'<th>{g_attr}</th>'
        table += '</tr></thead>'
        table += '<tbody>'
        for pressure in pressures:
            table += '<tr>'
            table += f'<td>{pressure.depth}</td>'
            p_attributes = pressure.attributes.all()
            if p_attributes.exists():
                for category in global_attrs:
                    attribute = p_attributes.get(attribute=category)
                    table += (f'<td><input type="checkbox" '
                              f'class="form-check form-check-inline" name="attr_{attribute.pk}" '
                              f'hx-post="{reverse_lazy('settingsdb:selected_attribute', args=(attribute.pk,))}" '
                              f'hx-swap="none"'
                              f'{"checked" if attribute.is_collected else ""}/></td>')
            table += '</tr>'
        table += '</tbody>'
        table += '</table>'
        body.append(HTML(table))
        body.append(
            Row(
                Hidden('station_id', self.initial['station'].pk),
                Column(
                    Field('depth', id='input_id_depth', css_class='form-control form-control-sm'),
                    submit_pressure,
                ),
                Column(
                    Field('attribute', id='input_id_attribute', css_class='form-select form-select-sm'),
                    submit_attributes,
                    id='div_id_col_attribute_input'
                ),
            ),
        )
        return body

    def __init__(self, *args, **kwargs):
        super().__init__(card_name="plan", card_title=_("Station Plan"), *args, **kwargs)

        if self.initial and 'station' in self.initial:
            attributes = settings_models.GlobalSampleTypeCategory.objects.exclude(
                attributes__plan__station=self.initial['station']).distinct()

            self.fields['attribute'].choices = [(None, '--------')]
            self.fields['attribute'].choices += [(st.id, st) for st in attributes]
            self.fields['attribute'].choices.append((-1, '-- New --'))

        self.fields['attribute'].widget.attrs["hx-trigger"] = 'change'
        self.fields['attribute'].widget.attrs["hx-swap"] = 'none'
        self.fields['attribute'].widget.attrs["hx-get"] = reverse_lazy('settingsdb:add_attribute')


class StationForm(forms.Form):

    station = forms.ChoiceField(label=_("Station"))
    latitude = forms.CharField(label=_("Latitude"))
    longitude = forms.CharField(label=_("Longitude"))
    sounding = forms.IntegerField(label=_("Sounding"))
    fixstation = forms.BooleanField(label=_("Fix Station"))

    @staticmethod
    def get_station_input_id():
        return "id_station_field"

    @staticmethod
    def get_card_content_id():
        return f"div_station_plan_content_id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        stations = settings_models.GlobalStation.objects.all().order_by("name")
        self.fields['station'].queryset = stations

        self.fields['station'].choices = [(None, '--------')]
        self.fields['station'].choices += [(st.id, st) for st in settings_models.GlobalStation.objects.all()]
        self.fields['station'].choices.append((-1, '-- New --'))

        if self.initial:
            station = settings_models.GlobalStation.objects.get(id=self.initial['station_id'])
            self.fields['station'].initial = station.pk
            self.fields['latitude'].initial = station.latitude
            self.fields['longitude'].initial = station.longitude
            self.fields['sounding'].initial = station.sounding
            self.fields['fixstation'].initial = station.fixstation

        station_kwargs = {
            'hx-get': reverse_lazy('settingsdb:form_station_selected')
        }

        content = Div(
            Row(
                Column(Field('station', css_class='form-control form-select-sm',
                             id=self.get_station_input_id(), **station_kwargs),
                       css_class='col-auto'),
                Column(Field('fixstation', css_class='form-check form-check-inline'), css_class="mb-1"),
                css_class='d-flex flex-row justify-content-start align-items-end',
            ),
            Row(
                Column(Field('latitude', css_class='form-control form-control-sm'),
                       css_class='col-sm-12 col-md-4'),
                Column(Field('longitude', css_class='form-control form-control-sm'),
                       css_class='col-sm-12 col-md-4'),
                Column(Field('sounding', css_class='form-control form-control-sm'),
                       css_class='col-sm-12 col-md-4'),
            ),
        )
        content_frame = Div(content, id=self.get_card_content_id())

        if self.initial and 'station_id' in self.initial:
            station = settings_models.GlobalStation.objects.get(id=self.initial['station_id'])
            station_plan_form = PlanForm(initial={"station": station} )
            station_plan_html = render_crispy_form(station_plan_form)
            station_plan_row = Row(
                Column(
                    HTML(station_plan_html),
                ),
                id=f'{self.get_card_content_id()}_plan'
            )
            content.fields.append(station_plan_row)

        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(content_frame)


def select_station(request, **kwargs):
    station_id = request.GET.get('station')

    station_form = StationForm(initial={'station_id': station_id})
    station_html = render_crispy_form(station_form)
    station_soup = BeautifulSoup(station_html, 'html.parser')

    root_div = station_soup.find('div')
    root_div.attrs['hx-swap'] = 'outerHTML'
    root_div.attrs['hx-swap-oob'] = 'true'

    return HttpResponse(station_soup)


def add_pressure(request):
    station_id = request.POST.get('station_id')
    depth = request.POST.get('depth')

    new_plan = settings_models.GlobalStationPlan(station_id=station_id, depth=depth)
    new_plan.save()

    station = settings_models.GlobalStation.objects.get(id=station_id)
    attrs = settings_models.GlobalSampleTypeCategory.objects.filter(attributes__plan__station=station).distinct()
    for attr in attrs:
        settings_models.GlobalStationAttribute(plan=new_plan, attribute=attr).save()

    plan_form = PlanForm(initial={'station': station})
    plan_html = render_crispy_form(plan_form)
    plan_soup = BeautifulSoup(plan_html, 'html.parser')
    plan_div = plan_soup.find('div')
    plan_div.attrs['hx-swap'] = 'outerHTML'
    plan_div.attrs['hx-swap-oob'] = 'true'

    return HttpResponse(plan_soup)

def add_attribute(request):
    soup = BeautifulSoup("", "html.parser")
    if request.method == 'GET':
        attribute = request.GET.get('attribute')

        if attribute == '-1':
            station_input = soup.new_tag('input')
            station_input.attrs['name'] = 'attribute'
            station_input.attrs['id'] = 'input_id_attribute'
            station_input.attrs['type'] = 'text'
            station_input.attrs['class'] = 'textinput form-control form-control-sm col'
            # station_input.attrs['hx-swap'] = 'outerHTML'
            station_input.attrs['hx-swap-oob'] = 'outerHTML'

            soup.append(station_input)

            return HttpResponse(soup)
    elif request.method == 'POST':
        attribute: str = request.POST.get('attribute')
        station_id = request.POST.get('station_id')
        station = settings_models.GlobalStation.objects.get(id=station_id)

        if attribute.isnumeric():
            category = settings_models.GlobalSampleTypeCategory.objects.get(pk=int(attribute))
        else:
            category = settings_models.GlobalSampleTypeCategory.objects.get_or_create(name=attribute)[0]

        for plan in station.plans.all():
            attr = settings_models.GlobalStationAttribute.objects.get_or_create(plan=plan, attribute=category)[0]

        plan_form = PlanForm(initial={'station': station})
        plan_html = render_crispy_form(plan_form)
        plan_soup = BeautifulSoup(plan_html, 'html.parser')

        plan_card = plan_soup.find('div')
        plan_card.attrs['hx-swap'] = 'outerHTML'
        plan_card.attrs['hx-swap-oob'] = 'true'

        soup.append(plan_soup)
        response = HttpResponse(soup)
        return response
        pass

    return HttpResponse()

def selected_attribute(request, attribute_id):
    global_attribute = settings_models.GlobalStationAttribute.objects.get(id=attribute_id)
    global_attribute.is_collected = not global_attribute.is_collected
    global_attribute.save()

    return HttpResponse()

url_prefix = "station/plan"
station_plan_urls = [
    path(f'{url_prefix}/selected/', select_station, name="form_station_selected"),

    path(f'{url_prefix}/pressure/add/', add_pressure, name="add_pressure"),
    path(f'{url_prefix}/attribute/add/', add_attribute, name="add_attribute"),
    path(f'{url_prefix}/attribute/selected/<int:attribute_id>/', selected_attribute, name="selected_attribute"),
]
