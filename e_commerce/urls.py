from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from .views import CustomPasswordResetView





from . import views

urlpatterns = [
    path("", views.index, name='index'),
    path('login/', LoginView.as_view(), name='login'),  # Vedi come viene definito qui il login
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('logout/', LogoutView.as_view(next_page='index'), name='logout'),
    path('validate-field-registration/', views.validate_field_registration, name='validate_field_registration'),
    path('prodotto/<int:prodotto_id>/', views.dettaglio_prodotto, name='dettaglio_prodotto'),
    path('user/carrello/', views.carrello, name='carrello'),
    path('add_to_cart/', views.aggiungi_al_carrello, name='add_to_cart'),
    path('rimuovi_dal_carrello/', views.rimuovi_dal_carrello, name='rimuovi_dal_carrello'),
    path('aggiorna_quantita/', views.aggiorna_quantita, name='aggiorna_quantita'),
    path('checkout/', views.checkout, name='checkout'),
    path('conferma-ordine/<int:ordine_id>/', views.conferma_ordine, name='conferma_ordine'),
    path('processa-ordine/', views.processa_ordine, name='processa_ordine'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
    path('salva-dati-spedizione/', views.salva_dati_spedizione, name='salva_dati_spedizione'),
    path('contattaci/', views.contattaci, name='contattaci'),
    path('contattaci/', views.conferma_ordine, name='conferma_ordine'),
    path('i_piu_venduti/', views.i_piu_venduti, name='i_piu_venduti'),
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('prodotto/<int:prodotto_id>/recensione/', views.aggiungi_recensione, name='aggiungi_recensione'),
    path('novita/', views.novita, name='novita'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 