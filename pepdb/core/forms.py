# coding: utf-8
from __future__ import unicode_literals
from django.forms import (
    ModelForm,
    Textarea,
    TextInput,
    Form,
    BooleanField,
    FileField,
    CheckboxInput,
)
from core.models import FeedbackMessage
from django.utils.translation import ugettext_lazy as _
from captcha.fields import ReCaptchaField


class FeedbackForm(ModelForm):
    captcha = ReCaptchaField()

    class Meta:
        model = FeedbackMessage
        fields = ["person", "text", "link", "email", "contacts", "read_and_agreed"]

        widgets = {
            "person": TextInput(
                attrs={"class": "form-control input-md", "placeholder": _("ПІБ")}
            ),
            "text": Textarea(
                attrs={
                    "class": "form-control",
                    "required": "",
                    "rows": "3",
                    "placeholder": _("Текст повідомлення"),
                }
            ),
            "link": TextInput(
                attrs={"class": "form-control input-md", "placeholder": _("http://")}
            ),
            "email": TextInput(
                attrs={
                    "class": "form-control input-md",
                    "required": "",
                    "placeholder": _("Ваш імейл"),
                }
            ),
            "contacts": TextInput(
                attrs={
                    "class": "form-control input-md",
                    "placeholder": _("Ваше ім'я та телефон"),
                }
            ),
            "read_and_agreed": CheckboxInput(
                attrs={
                    "class": "input-md check__input",
                    "required": "",
                    "placeholder": _(
                        "Я прочитав запитання, які часто задаються та не знайшов відповіді"
                    ),
                }
            ),
        }


class EDRImportForm(Form):
    csv = FileField(required=True)
    is_state_companies = BooleanField(
        required=False, help_text="Керівники усіх компанії з файлу є ПЕПами"
    )


class ForeignImportForm(Form):
    csv = FileField(required=True)


class ZIPImportForm(Form):
    zipfile = FileField(required=True, label="ZIP-файл")

