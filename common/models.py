from django.db import models


class DrupalFields(models.Model):
    drupal_node_id = models.IntegerField(null=True, blank=True)
    drupal_body_migrated = models.TextField(null=True, blank=True)
    drupal_path = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True
