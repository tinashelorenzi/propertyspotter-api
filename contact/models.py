from django.db import models

# Create your models here.

class ContactEntry(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Contact from {self.name} ({self.email})"

    class Meta:
        verbose_name = "Contact Entry"
        verbose_name_plural = "Contact Entries"
        ordering = ['-created_at']
