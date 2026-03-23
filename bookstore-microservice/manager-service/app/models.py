from django.db import models


class Manager(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    level = models.CharField(max_length=50, default='manager')

    def __str__(self):
        return f"{self.name} ({self.level})"
