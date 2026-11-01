from django.db import models


class Question(models.Model):
    """A question whose answer is a whole number, 0 or greater (R6, R9)."""

    text = models.CharField(max_length=255)
    # Big integer so answers like world population (8 000 000 000) fit.
    answer = models.PositiveBigIntegerField()
    category = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.text
