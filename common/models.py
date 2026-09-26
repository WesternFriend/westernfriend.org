from django.db import models


class DrupalFields(models.Model):
    drupal_node_id = models.IntegerField(null=True, blank=True)

    class Meta:
        abstract = True
