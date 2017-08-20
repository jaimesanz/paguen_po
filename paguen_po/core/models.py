# -*- coding: utf-8 -*-
import uuid as uuid_lib

from django.db import models


class UUIDModel(models.Model):
    """Provides UUID field for a model."""

    class Meta:
        abstract = True

    uuid = models.UUIDField(
        db_index=True,
        default=uuid_lib.uuid4,
        editable=False
    )
