from django.contrib import admin
from .models import Prodotto, ProdottoTaglie, Taglia
from .models import CustomUser
from .models import ProductImage
from django.contrib.auth.admin import UserAdmin
from .models import Ordine



class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'ruolo', 'nome', 'cognome', 'indirizzo', 'numero_di_telefono']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('ruolo', 'nome', 'cognome', 'indirizzo', 'numero_di_telefono')}),
    )
    
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Prodotto)
admin.site.register(ProductImage)
admin.site.register(Taglia)
admin.site.register(ProdottoTaglie)
admin.site.register(Ordine)


