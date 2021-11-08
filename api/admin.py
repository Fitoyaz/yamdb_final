from django.contrib import admin

from api.models import Category, Genre, Title


class CategoriesAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'slug', 'category_description',)
    search_fields = ('name', 'slug',)
    empty_value_display = '-пусто-'


class GenresAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'slug', 'genre_description', )
    search_fields = ('name', 'slug',)
    empty_value_display = '-пусто-'


class TitlesAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'year',
        'description',
        # 'genre',
        'category',
    )
    search_fields = ('name', 'year', 'category')
    list_filter = ('year', 'category')
    empty_value_display = '-пусто-'


admin.site.register(Category, CategoriesAdmin)
admin.site.register(Genre, GenresAdmin)
admin.site.register(Title, TitlesAdmin)
