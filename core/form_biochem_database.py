import datetime
import os.path
import time

from bs4 import BeautifulSoup
from crispy_forms.bootstrap import StrictButton
from crispy_forms.layout import Column, Row, Field, HTML, Div
from crispy_forms.utils import render_crispy_form
from django import forms
from django.conf import settings
from django.core.cache import caches
from django.db import DatabaseError
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from render_block import render_block_to_string

import biochem.upload
import dart2.settings
from core import models
from core import forms as core_forms
from core.htmx import send_user_notification_queue, send_user_notification_close
from core.validation import validate_samples_for_biochem
from dart2.utils import load_svg

import logging

logger = logging.getLogger('dart')


def get_crispy_element_attributes(element):
    attr_dict = {k: v.replace("\"", "") for k, v in [attr.split('=') for attr in element.flat_attrs.strip().split(" ")]}
    return attr_dict


class BiochemUploadForm(core_forms.CollapsableCardForm, forms.ModelForm):
    selected_database = forms.ChoiceField(required=False)
    db_password = forms.CharField(widget=forms.PasswordInput(render_value=True), required=False)

    # I had to override the default Bootstrap template for fields, because someone thought putting 'mb-3'
    # as a default for field wrappers was a good idea and it creates a massive gap under the inputs when
    # used in a card title
    field_template = os.path.join(dart2.settings.TEMPLATE_DIR, "field.html")

    class Meta:
        model = models.BcDatabaseConnection
        fields = ['account_name', 'name', 'host', 'port', 'engine', 'selected_database', 'db_password']

    def get_db_select(self):
        url = reverse_lazy('core:hx_validate_database_connection', args=(self.mission_id,))

        title_id = f"control_id_database_select_{self.card_name}"

        db_select_attributes = {
            'id': title_id,
            'class': 'form-select form-select-sm',
            'name': 'selected_database',
            'hx-get': url,
            'hx-swap': 'none'
        }
        db_select = Column(
            Row(
                Column(
                    HTML('<label class="me-2 pt-1" for="' + title_id + '">' + _("Biochem Database") + '</label>'),
                    Field('selected_database', template=self.field_template, **db_select_attributes,
                          wrapper_class='col-auto'),
                    css_class='input-group input-group-sm'
                ),
            ),
            id=f"div_id_db_select_{self.card_name}",
            css_class="col-auto"
        )

        return db_select

    def get_db_password(self):
        connect_button_icon = load_svg('plug')

        connect_button_id = f'btn_id_connect_{self.card_name}'
        url = reverse_lazy('core:hx_validate_database_connection', args=(self.mission_id,))

        connect_button_class = "btn btn-primary btn-sm"
        if 'selected_database' in self.initial and self.initial['selected_database']:
            sentinel = object()
            password = caches['biochem_keys'].get("pwd", sentinel, version=self.initial['selected_database'])
            if password is not sentinel:
                connect_button_class = "btn btn-success btn-sm"

        connect_button_attrs = {
            'id': connect_button_id,
            'name': 'connect',
            'hx-get': url,
            'hx-swap': 'none'
        }
        connect_button = StrictButton(connect_button_icon, css_class=connect_button_class, **connect_button_attrs)

        password_field_label = f'control_id_password_{self.card_name}'
        password_field = Column(
            Row(
                Column(
                    HTML(
                        '<label class="me-2 pt-1" for="' + password_field_label + '">' + _("Password") + '</label>'
                    ),
                    Field('db_password', id=password_field_label,
                          template=self.field_template, css_class="form-control form-control-sm"),
                    connect_button,
                    css_class='input-group input-group-sm'
                ),
            ),
            id=f"div_id_db_password_{self.card_name}",
            css_class="col"
        )

        return password_field

    def get_upload(self):
        url = reverse_lazy('core:hx_upload_bio_chem', args=(self.mission_id,))
        upload_button_icon = load_svg('database-add')
        upload_button_id = f'btn_id_upload_{self.card_name}'
        upload_button_attrs = {
            'id': upload_button_id,
            'name': 'upload',
            'hx-get': url,
            'hx-swap': 'none'
        }
        upload_button = StrictButton(upload_button_icon, css_class='btn btn-sm btn-primary', **upload_button_attrs)

        upload_field = Column(
            Div(id='div_id_upload_sensor_type_list'),
            upload_button,
            id=f"div_id_db_upload_{self.card_name}",
            css_class="col-auto"
        )

        return upload_field

    def get_card_title(self):
        title = super().get_card_title()

        title.append(self.get_db_select())
        title.append(self.get_db_password())
        title.append(self.get_upload())

        return title

    def get_alert_area(self):
        msg_row = Row(id=f"div_id_biochem_alert_{self.card_name}")
        return msg_row

    def get_card_header(self):
        header = super().get_card_header()
        header.append(self.get_alert_area())
        return header

    def get_card_body(self):
        body = super().get_card_body()

        button_column = Column(css_class='align-self-center mb-1')

        url = reverse_lazy('core:hx_validate_database_connection', args=(self.mission_id,))

        input_row = Row(
            Column(Field('account_name')),
            Column(Field('name')),
            Column(Field('host')),
            Column(Field('port')),
            Column(Field('engine')),
            button_column,
            id="div_id_biochem_db_details_input"
        )

        if self.instance and self.instance.pk:
            update_attrs = {
                'id': 'btn_id_db_details_update',
                'title': _('Update'),
                'name': 'update_db',
                'value': self.instance.pk,
                'hx_get': url,
                'hx_swap': 'none'
            }
            icon = load_svg('arrow-clockwise')
            update_button = StrictButton(icon, css_class="btn btn-primary btn-sm", **update_attrs)
            button_column.append(update_button)
        else:
            add_attrs = {
                'id': 'btn_id_db_details_add',
                'title': _('Add'),
                'name': 'add_db',
                'hx_get': url,
                'hx_swap': 'none'
            }
            icon = load_svg('plus-square')
            add_button = StrictButton(icon, css_class="btn btn-primary btn-sm", **add_attrs)
            button_column.append(add_button)

        body.append(input_row)

        return body

    # at a minimum a mission_id must be supplied in
    def __init__(self, mission_id, *args, **kwargs):
        self.mission_id = mission_id
        super().__init__(*args, **kwargs, card_name="biochem_db_details")

        self.fields['selected_database'].label = False
        self.fields['db_password'].label = False

        databases = models.BcDatabaseConnection.objects.all()
        self.fields['selected_database'].choices = [(db.id, db) for db in databases]
        self.fields['selected_database'].choices.insert(0, (None, '--- New ---'))

        if 'selected_database' in self.initial:
            database_id = int(self.initial['selected_database'])
            sentinel = object()
            password = caches['biochem_keys'].get('pwd', sentinel, version=database_id)
            if password is not sentinel:
                self.fields['db_password'].initial = password


def update_connection_button(soup: BeautifulSoup, mission_id, post: bool = False, error: bool = False):
    url = reverse_lazy('core:hx_validate_database_connection', args=(mission_id,))

    icon = BeautifulSoup(load_svg('plug'), 'html.parser').svg

    button = soup.new_tag('button')
    button.attrs = {
        'id': "btn_id_connect_biochem_db_details",
        'name': "connect",
        'hx-swap-oob': 'true',
    }
    if post:
        button.attrs['hx-post'] = url
        button.attrs['hx-trigger'] = 'load'
        button.attrs['disabled'] = 'true'
        button.attrs['class'] = "btn btn-disable btn-sm"
    else:
        button.attrs['hx-get'] = url
        if error:
            button.attrs['class'] = "btn btn-danger btn-sm"
        else:
            sentinel = object()
            password = sentinel
            database_id = caches['biochem_keys'].get('database_id', sentinel)
            if database_id is not sentinel:
                password = caches['biochem_keys'].get('pwd', sentinel, version=database_id)

            button.attrs['class'] = "btn btn-primary btn-sm"
            if password is not sentinel:
                button.attrs['class'] = "btn btn-success btn-sm"
                button.attrs['name'] = "disconnect"

    button.append(icon)
    soup.append(button)


def validate_database(request, **kwargs):

    mission_id = kwargs['mission_id']
    if request.method == "GET":
        if 'add_db' in request.GET or 'update_db' in request.GET:
            soup = BeautifulSoup('', 'html.parser')
            msg_div = soup.new_tag('div')
            msg_div.attrs = {
                'id': 'div_id_biochem_alert_biochem_db_details',
                'hx-swap-oob': 'true'
            }
            soup.append(msg_div)

            url = reverse_lazy('core:hx_validate_database_connection')
            attrs = {
                'component_id': 'div_id_biochem_alert',
                'message': _("Adding Database"),
                'hx-post': url,
                'hx-trigger': 'load'
            }
            alert_soup = core_forms.save_load_component(**attrs)
            msg_div.append(alert_soup)

            if 'add_db' in request.GET:
                # if we're adding a new DB, remove the selected input field containing the pk for the db instance
                select = soup.new_tag('select')
                select.attrs = {
                    'id': 'select_id_db_details',
                    'hx-swap-oob': 'true'
                }
                soup.append(select)

            return HttpResponse(soup)
        elif 'selected_database' in request.GET:
            # if the selected database changes update the form to show the selection
            database_id = request.GET['selected_database']
            password = None
            sentinal = object()
            if caches['biochem_keys'].get('database_id', sentinal) is not sentinal:
                if caches['biochem_keys'].get('pwd', sentinal, version=database_id) is not sentinal:
                    password = caches['biochem_keys'].get('pwd', version=database_id)

            if database_id:
                database = models.BcDatabaseConnection.objects.get(pk=database_id)
                db_form = BiochemUploadForm(mission_id, instance=database)
                caches['biochem_keys'].set('database_id', database.pk, 3600)
            else:
                db_form = BiochemUploadForm(mission_id)
                caches['biochem_keys'].delete('database_id')

            form_html = render_crispy_form(db_form)
            soup = BeautifulSoup(form_html, 'html.parser')

            body_attrs = get_crispy_element_attributes(db_form.get_card_body())
            soup.find(id=body_attrs['id']).attrs['hx-swap-oob'] = 'true'

            password_soup = soup.find(id="control_id_password_biochem_db_details")
            password_soup.attrs['hx-swap-oob'] = 'true'
            password_soup.attrs['value'] = password

            update_connection_button(soup, mission_id)

            return HttpResponse(soup)
        elif 'connect' in request.GET:
            soup = BeautifulSoup('', 'html.parser')
            update_connection_button(soup, mission_id, post=True)
            return HttpResponse(soup)
        elif 'disconnect' in request.GET:
            # if the user disconnects clear the password from the cache and set the connection button
            # back to it's origional state.
            soup = BeautifulSoup('', 'html.parser')

            sentinel = object()
            database_id = caches['biochem_keys'].get('database_id', sentinel)
            if database_id is not sentinel:
                caches['biochem_keys'].delete('pwd', version=database_id)

                db_form = BiochemUploadForm(mission_id, initial={'selected_database': database_id})
                db_form_html = render_crispy_form(db_form)

                title_attributes = get_crispy_element_attributes(db_form.get_card_title())
                soup = BeautifulSoup(db_form_html, 'html.parser')
                soup.find(id=title_attributes['id']).attrs['hx-swap-oob'] = 'true'

            update_connection_button(soup, mission_id)
            return HttpResponse(soup)
    else:
        soup = BeautifulSoup('', 'html.parser')
        msg_div = soup.new_tag('div')
        msg_div.attrs = {
            'id': "div_id_biochem_alert_biochem_db_details",
            'hx-swap-oob': 'true'
        }
        soup.append(msg_div)

        if 'connect' in request.POST:
            database_id = request.POST['selected_database']
            password = request.POST['db_password']

            database = models.BcDatabaseConnection.objects.get(pk=database_id)
            settings.DATABASES['biochem'] = database.connect(password=password)
            connection_success = False

            # we don't care about the table name in this case, we're just checking the connection
            bcs_d = biochem.upload.get_bcs_d_model('connection_test')
            try:
                # either we'll get a 942 error indicating the connection worked by the table doesn't exist
                # or the connection worked and the table does exist. Any other reason the connection failed.
                bcs_d.objects.exists()
                connection_success = True
            except DatabaseError as e:

                if e.args[0].code == 942:
                    # A 942 Oracle error means the connection worked, but the table/objects don't exist.
                    connection_success = True
                elif e.args[0].code == 12545:
                    # A 12545 Oracle error means there's an issue with the database connection.
                    # This could be because the user isn't logged in on VPN so the Oracle DB can't be connected to.
                    message = _("No connection to database, this may be due to VPN (see ./logs/error.log)")
                    alert_soup = core_forms.blank_alert(component_id="div_id_upload_biochem", alert_type="danger",
                                                        message=message)
                    soup.append(alert_soup)
                elif e.args[0].code == 1017:
                    message = _("Invalid username/password; login denied")
                    alert_soup = core_forms.blank_alert(component_id="div_id_upload_biochem", alert_type="danger",
                                                        message=message)
                    soup.append(alert_soup)
                else:
                    logger.exception(e)
                    message = _("An unexpected database error occured. (see ./logs/error.log)")
                    alert_soup = core_forms.blank_alert(component_id="div_id_upload_biochem", alert_type="danger",
                                                        message=message)
                    soup.append(alert_soup)

            if connection_success:
                caches['biochem_keys'].set('database_id', database_id, 3600)
                caches['biochem_keys'].set(f'pwd', password, 3600, version=database_id)

            # since we have a DB password in the cache we'll update the page
            # to indicate we're connected or there was an issue
            update_connection_button(soup, mission_id, post=False, error=(not connection_success))

            return HttpResponse(soup)
        else:
            soup = BeautifulSoup('', 'html.parser')
            div = soup.new_tag('div')
            div.attrs = {
                'id': 'div_id_biochem_alert_biochem_db_details',
                'hx-swap-oob': 'true'
            }
            soup.append(div)

            update_connection_button(soup, mission_id)

            if 'selected_database' in request.POST and request.POST['selected_database']:
                database = models.BcDatabaseConnection.objects.get(pk=request.POST['selected_database'])
                db_form = BiochemUploadForm(request.POST, instance=database)
            else:
                db_form = BiochemUploadForm(request.POST)

            if db_form.is_valid():
                # if the form is valid we'll render it then send back the elements of the form that have to change
                # basically just the selected database dropdown and clear the password field, so just the title bar
                db_details = db_form.save()

                # set the selected database to the updated/saved value
                new_db_form = BiochemUploadForm(initial={'selected_database': db_details.pk})
                selected_db_block = render_crispy_form(new_db_form)

                title_attributes = get_crispy_element_attributes(new_db_form.get_card_title())

                selected_db_soup = BeautifulSoup(selected_db_block, 'html.parser')
                selected_db_soup.find(id=title_attributes['id']).attrs['hx-swap-oob'] = 'true'
                soup.append(selected_db_soup)
            else:
                form_errors = render_crispy_form(db_form)
                form_soup = BeautifulSoup(form_errors, 'html.parser')
                form_soup.find(id="div_id_biochem_db_details_input").attrs['hx-swap-oob'] = 'true'

                soup.append(form_soup)

            return HttpResponse(soup)


def upload_bio_chem(request, **kwargs):
    mission_id = kwargs['mission_id']

    soup = BeautifulSoup('', 'html.parser')
    div = soup.new_tag('div')
    div.attrs = {
        'id': "div_id_biochem_alert_biochem_db_details",
        'hx-swap-oob': 'true'
    }
    soup.append(div)

    #check that the database and password were set in the cache
    sentinel = object()
    database_id = caches['biochem_keys'].get('database_id', default=sentinel)
    password = caches['biochem_keys'].get(f'pwd', default=sentinel, version=database_id)
    if database_id is sentinel or password is sentinel:
        attrs = {
            'component_id': 'div_id_upload_biochem',
            'alert_type': 'danger',
            'message': _("Database connection is unavailable, reconnect and try again."),
        }
        alert_soup = core_forms.blank_alert(**attrs)
        div.append(alert_soup)

        return HttpResponse(soup)

    if request.method == "GET":

        attrs = {
            'component_id': 'div_id_upload_biochem',
            'alert_type': 'info',
            'message': _("Uploading"),
            'hx-post': reverse_lazy('core:hx_upload_bio_chem', args=(mission_id,)),
            'hx-swap': 'none',
            'hx-trigger': 'load',
            'hx-target': "#div_id_biochem_alert_biochem_db_details",
            'hx-ext': "ws",
            'ws-connect': "/ws/biochem/notifications/"
        }
        alert_soup = core_forms.save_load_component(**attrs)

        # add a message area for websockets
        msg_div = alert_soup.find(id="div_id_upload_biochem_message")
        msg_div.string = ""

        # The core.consumer.processing_elog_message() function is going to write output to a div
        # with the 'status' id, we'll stick that in the loading alerts message area and bam! Instant notifications!
        msg_div_status = soup.new_tag('div')
        msg_div_status['id'] = 'status'
        msg_div_status.string = _("Loading")
        msg_div.append(msg_div_status)
        div.append(alert_soup)

    elif request.method == "POST":
        mission = models.Mission.objects.get(pk=mission_id)
        try:
            samples = models.Sample.objects.filter(bottle__event__mission=mission)
            data_types = [dt for dt in models.DiscreteSampleValue.objects.filter(
                sample__in=samples).values_list('sample_datatype', flat=True).distinct()]

            # have a couple second pause for the websocket to finish initializing.
            time.sleep(2)
            logger.info("Sending user notification")
            send_user_notification_queue('biochem', _("Validating Sensor/Sample Datatypes"))

            models.Error.objects.filter(mission=mission).delete()

            errors = validate_samples_for_biochem(mission)

            if errors:
                send_user_notification_queue('biochem', _("Datatypes missing see errors"))
                models.Error.objects.bulk_create(errors)

            # The mission_samples.html page has a websocket notifications element on it. We can send messages
            # to the notifications element to display progress to the user, but we can also use it to
            # send an update request to the page when loading is complete.
            url = reverse_lazy("core:hx_get_biochem_errors", args=(mission.pk,))
            hx = {
                'hx-get': url,
                'hx-trigger': 'load',
                'hx-target': '#div_id_upload_biochem',
                'hx-swap': 'outerHTML',
                'message': _("Datatype validation complete")
            }
            send_user_notification_close('biochem', **hx)

            # 1) get bottles from BCS_D table
            bcs_d = biochem.upload.get_bcs_d_model(mission.get_biochem_table_name)
            exists = biochem.upload.check_and_create_model('biochem', bcs_d)

            # 2) if the BCS_D table doesn't exist, create with all the bottles
            bottles = models.Bottle.objects.filter(event__mission=mission)
            if exists:
                # 3) else filter bottles from local db where bottle.last_modified > bcs_d.created_date
                last_uploaded = bcs_d.objects.all().values_list('created_date', flat=True).distinct().last()
                if last_uploaded:
                    bottles = bottles.filter(last_modified__gt=last_uploaded)

            if bottles.exists():
                # 4) upload only bottles that are new or were modified since the last biochem upload
                biochem.upload.upload_bcs_d('upsonp', bcs_d, bottles)

            # upload the BCD, the Sample data
            # 1) get the biochem BCD_D model
            bcd_d = biochem.upload.get_bcd_d_model(mission.get_biochem_table_name)
            exists = biochem.upload.check_and_create_model('biochem', bcd_d)

            # 2) if the BCD_D model doesn't exist create it and add all samples specified by sample_id
            if exists:
                # 3) else filter the samples down to rows based on:
                # 3a) samples.type = sample_id
                # 3b) samples.last_upload_date < bcd_d.created_date
                last_uploaded = bcd_d.objects.filter(dis_detail_data_type_seq__in=data_types).values_list(
                    'created_date', flat=True).distinct().last()
                samples = models.DiscreteSampleValue.objects.filter(sample__bottle__event__mission=mission)
                # if last_uploaded:
                #     samples = samples.filter(bio_upload_date__lt=last_uploaded)

            if samples.exists():
                # 4) upload only samples that are new or were modified since the last biochem upload
                biochem.upload.upload_bcd_d('upsonp', bcd_d, samples)
                for sample in samples:
                    sample.bio_upload_date = datetime.datetime.now().strftime("%Y-%m-%d")
                models.DiscreteSampleValue.objects.bulk_update(samples, ['bio_upload_date'])

            # bcd_d = biochem.upload.get_or_create_bcd_d_model(db_name, mission.name)
        except DatabaseError as e:
            caches['biochem_keys'].delete('pwd', version=database_id)
            update_connection_button(soup, mission_id, error=True)
            logger.exception(e)

            # A 12545 Oracle error means there's an issue with the database connection. This could be because
            # the user isn't logged in on VPN so the Oracle DB can't be connected to.
            if e.args[0].code == 12545:
                attrs = {
                    'component_id': 'div_id_upload_biochem',
                    'alert_type': 'danger',
                    'message': f'{e.args[0].code} : ' + _("Issue connecting to database, "
                                                  "this may be due to VPN. (see ./logs/error.log)."),
                }
            else:
                attrs = {
                    'component_id': 'div_id_upload_biochem',
                    'alert_type': 'danger',
                    'message': f'{e.args[0].code} : ' + _("An unknown database issue occurred (see ./logs/error.log)."),
                }

            alert_soup = forms.blank_alert(**attrs)
            div.append(alert_soup)

    return HttpResponse(soup)


def get_biochem_errors(request, **kwargs):
    mission_id = kwargs['mission_id']
    if request.method == 'GET':
        context = {
            'mission': models.Mission.objects.get(pk=mission_id),
            'biochem_errors': models.Error.objects.filter(mission_id=mission_id, type=models.ErrorType.biochem)
        }
        html = render_to_string(template_name='core/partials/card_biochem_validation.html', context=context)

        return HttpResponse(html)
    return Http404("You shouldn't be here")


def add_sensor_to_upload(request, **kwargs):
    if request.method == 'POST':
        if 'add_sensor' in request.POST:
            pass
        return HttpResponse()