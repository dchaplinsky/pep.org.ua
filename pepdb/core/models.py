# coding: utf-8
from __future__ import unicode_literals


from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.admin.models import LogEntry

from core.model.persons import Person
from core.model.companies import Company, CompanyCategories
from core.model.countries import Country
from core.model.declarations import (
    Declaration,
    DeclarationExtra,
    DeclarationToLink,
    DeclarationToWatch,
)
from core.model.translations import Ua2RuDictionary, Ua2EnDictionary
from core.model.connections import (
    Person2Person,
    Person2Company,
    Company2Company,
    Person2Country,
    Company2Country,
    RelationshipProof,
)
from core.model.flags import Rule, Flag
from core.model.articles import Article
from core.model.supplementaries import ActionLog, Document, FeedbackMessage

__all__ = [
    Person,
    Company,
    Country,
    Declaration,
    DeclarationExtra,
    Ua2EnDictionary,
    Ua2RuDictionary,
    Person2Person,
    Person2Country,
    Person2Company,
    Company2Company,
    Person2Country,
    Company2Country,
    ActionLog,
    Document,
    FeedbackMessage,
    RelationshipProof,
    DeclarationToLink,
    DeclarationToWatch,
    CompanyCategories,
    Rule,
    Flag,
    Article,
]


@receiver(post_save, sender=LogEntry, dispatch_uid="touch_editor_signal")
def touch_last_editor(sender, **kwargs):
    if "instance" not in kwargs:
        return

    if not kwargs.get("created", False):
        return

    instance = kwargs["instance"]
    obj = instance.get_edited_object()

    if isinstance(obj, (Person, Company)):
        obj.last_change = timezone.now()
        obj.last_editor = instance.user
        obj.save()
