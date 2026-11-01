from urllib.parse import urlencode

from django.contrib import admin

from .models import Game, Player, Question


class PlayerInline(admin.TabularInline):
    model = Player
    extra = 0


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ["__str__", "total_rounds"]
    inlines = [PlayerInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["text", "answer", "category", "created_at"]
    list_filter = ["category"]
    search_fields = ["text"]

    def response_add(self, request, obj, post_url_continue=None):
        """After "Save and add another", prefill the new form with the same category.

        The admin fills the add form with values from the URL (?category=...),
        so we only need to add the category to the address it redirects to.
        """
        response = super().response_add(request, obj, post_url_continue)
        if "_addanother" in request.POST and obj.category:
            separator = "&" if "?" in response["Location"] else "?"
            response["Location"] += separator + urlencode({"category": obj.category})
        return response
