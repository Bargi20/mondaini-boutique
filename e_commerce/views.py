from datetime import timezone
from django.shortcuts import get_object_or_404, render,redirect
from django.urls import reverse
from .models import Prodotto, ProdottoTaglie, ProductImage, OrdineProdotto, CustomUser,Ordine, Recensione, Taglia
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Ordine
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.decorators.http import require_POST
from django.db.models import Avg





from django.http import JsonResponse

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def index(request):
    # Recupera i parametri dalla query string
    tipo_filtro = request.GET.get('tipo', None)
    categoria_filtro = request.GET.get('categoria', None)
    search_query = request.GET.get('search', None)
    
    # Inizia con tutti i prodotti
    prodotti = Prodotto.objects.all().prefetch_related('images')
    
    # Applica i filtri se presenti
    if tipo_filtro:
        prodotti = prodotti.filter(tipo=tipo_filtro)
    
    if categoria_filtro:
        prodotti = prodotti.filter(categoria=categoria_filtro)
    
    if search_query:
        prodotti = prodotti.filter(nome__icontains=search_query)

    # Se è una richiesta AJAX, restituisci i dati in formato JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        prodotti_data = []
        for prodotto in prodotti:
            immagine_url = prodotto.images.first().image.url if prodotto.images.exists() else None
            prodotti_data.append({
                'id': prodotto.id,
                'nome': prodotto.nome,
                'prezzo': str(prodotto.prezzo),
                'categoria': prodotto.get_categoria_display(),
                'immagine_url': immagine_url,
                'url': request.build_absolute_uri(reverse('dettaglio_prodotto', args=[prodotto.id]))
            })
        
        return JsonResponse({
            'prodotti': prodotti_data
        })

    # Altrimenti, renderizza il template normalmente
    context = {
        'prodotti': prodotti,
        'tipo_filtro': tipo_filtro,
        'categorie': Prodotto.CATEGORIE_CHOICES,
    }
    return render(request, 'e_commerce/index.html', context)
   
    # Recupera i parametri dalla query string
    tipo_filtro = request.GET.get('tipo', None)
    categoria_filtro = request.GET.get('categoria', None)
    search_query = request.GET.get('search', None)
    page = request.GET.get('page', 1)
    per_page = 6  # Numero di prodotti per pagina
    
    # Inizia con tutti i prodotti
    prodotti = Prodotto.objects.all().prefetch_related('images')
    
    # Applica i filtri se presenti
    if tipo_filtro:
        prodotti = prodotti.filter(tipo=tipo_filtro)
    
    if categoria_filtro:
        prodotti = prodotti.filter(categoria=categoria_filtro)
    
    if search_query:
        prodotti = prodotti.filter(nome__icontains=search_query)

    # Crea il paginatore
    paginator = Paginator(prodotti, per_page)
    
    try:
        prodotti_paginati = paginator.page(page)
    except PageNotAnInteger:
        prodotti_paginati = paginator.page(1)
    except EmptyPage:
        prodotti_paginati = paginator.page(paginator.num_pages)

    # Se è una richiesta AJAX, restituisci i dati in formato JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        prodotti_data = []
        for prodotto in prodotti_paginati:
            immagine_url = prodotto.images.first().image.url if prodotto.images.exists() else None
            prodotti_data.append({
                'id': prodotto.id,
                'nome': prodotto.nome,
                'prezzo': str(prodotto.prezzo),
                'categoria': prodotto.get_categoria_display(),
                'immagine_url': immagine_url,
                'url': request.build_absolute_uri(reverse('dettaglio_prodotto', args=[prodotto.id]))
            })
        
        return JsonResponse({
            'prodotti': prodotti_data,
            'has_next': prodotti_paginati.has_next(),
            'has_previous': prodotti_paginati.has_previous(),
            'current_page': prodotti_paginati.number,
            'total_pages': paginator.num_pages,
            'total_products': paginator.count
        })

    # Altrimenti, renderizza il template normalmente
    context = {
        'prodotti': prodotti_paginati,
        'tipo_filtro': tipo_filtro,
        'categorie': Prodotto.CATEGORIE_CHOICES,
    }
    return render(request, 'e_commerce/index.html', context)



# Registrazione
def register_view(request):
    User = get_user_model()
    
    if request.method == 'POST':
        # Recupera i dati dal form
        username = request.POST.get('username')
        nome = request.POST.get('nome')
        cognome = request.POST.get('cognome')
        numero_di_telefono = request.POST.get('numero_di_telefono')
        indirizzo = request.POST.get('indirizzo')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Controlla se le password corrispondono
        if password != confirm_password:
            messages.error(request, 'Le password non corrispondono.')
            return render(request, 'registration/register.html', {'form_data': request.POST})

        # Controlla se username o email già esistono
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username già esistente.')
            return render(request, 'registration/register.html', {'form_data': request.POST})

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email già registrata.')
            return render(request, 'registration/register.html', {'form_data': request.POST})

        # Crea l'utente
        try:
            user = User.objects.create_user(
                username=username,
                nome=nome,
                cognome=cognome,
                indirizzo=indirizzo,
                numero_di_telefono=numero_di_telefono,
                email=email,
                password=password
            )
            user.save()
            messages.success(request, 'Registrazione completata! Ora puoi effettuare il login.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Errore durante la registrazione: {str(e)}')
            return render(request, 'registration/register.html', {'form_data': request.POST})

    # GET Request
    return render(request, 'registration/register.html')


@require_POST
def validate_field_registration(request):
    User = get_user_model()
    field = request.POST.get('field')
    value = request.POST.get('value')
    
    # Non validare nome e cognome lato server
    if field in ['nome', 'cognome']:
        return JsonResponse({
            'is_valid': True,
            'error': ''
        })
    
    # Validazione per email
    if field == 'email':
        if User.objects.filter(email=value).exists():
            return JsonResponse({
                'is_valid': False,
                'error': 'Questa email è già registrata'
            })
        if not value or '@' not in value or '.' not in value:
            return JsonResponse({
                'is_valid': False,
                'error': 'Inserisci un\'email valida'
            })
        
    elif field == 'username':
        if not value.isalnum() or len(value) < 3:
            return JsonResponse({
                'is_valid': False,
                'error': 'Lo username deve contenere solo lettere e numeri e deve essere lungo almeno 3 caratteri'
            })
        else:
            if User.objects.filter(username=value).exists():
                return JsonResponse({
                'is_valid': False,
                'error': 'Questo username è già in uso'
                })
    
    
    
    # Validazione per numero di telefono
    elif field == 'numero_di_telefono':
        if not value.isdigit() or len(value) < 9 or len(value) > 15:
            return JsonResponse({
                'is_valid': False,
                'error': 'Inserisci un numero di telefono valido'
            })
    
    # Validazione per indirizzo
    elif field == 'indirizzo':
        if len(value.strip()) < 5:
            return JsonResponse({
                'is_valid': False,
                'error': 'Inserisci un indirizzo valido'
            })
    
    # Validazione per password
    elif field == 'password':
        if len(value) < 8:
            return JsonResponse({
                'is_valid': False,
                'error': 'La password deve contenere almeno 8 caratteri'
            })
    
    # Se non ci sono errori
    return JsonResponse({
        'is_valid': True,
        'error': ''
    })

# Login
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Credenziali non valide.')
    return render(request, 'registration/login.html')

# Logout
def logout_view(request):
    logout(request)
    return redirect('index')



def dettaglio_prodotto(request, prodotto_id):
    prodotto = Prodotto.objects.get(id=prodotto_id)
    immagini = prodotto.images.all()
    
    # Recupera tutte le taglie standard
    tutte_le_taglie = Taglia.objects.all().order_by('id')
    taglie_prodotto = {pt.taglia_id: pt.quantita for pt in prodotto.prodotto_taglie.all()}
    
    # Informazioni taglie
    taglie_info = [
        {
            'taglia': taglia,
            'disponibile': taglie_prodotto.get(taglia.id, 0) > 0,
            'quantita': taglie_prodotto.get(taglia.id, 0)
        }
        for taglia in tutte_le_taglie
    ]
    
    # Recupera recensioni e calcola media
    recensioni = prodotto.recensioni.all()
    media_valutazioni = recensioni.aggregate(Avg('valutazione'))['valutazione__avg'] or 0
    numero_recensioni = recensioni.count()
    
    # Verifica se l'utente ha già recensito
    ha_recensito = False
    if request.user.is_authenticated:
        ha_recensito = recensioni.filter(utente=request.user).exists()
    
    context = {
        'prodotto': prodotto,
        'immagini': immagini,
        'taglie_info': taglie_info,
        'recensioni': recensioni,
        'media_valutazioni': round(media_valutazioni, 1),
        'numero_recensioni': numero_recensioni,
        'ha_recensito': ha_recensito,
    }
    return render(request, 'prodotto/dettaglio_prodotto.html', context)



@login_required
def aggiungi_recensione(request, prodotto_id):
    if request.method == 'POST':
        try:
            prodotto = Prodotto.objects.get(id=prodotto_id)
            valutazione = int(request.POST.get('valutazione'))
            commento = request.POST.get('commento')
            
            # Verifica se l'utente ha già recensito
            if Recensione.objects.filter(prodotto=prodotto, utente=request.user).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Hai già recensito questo prodotto'
                })
            
            # Crea la recensione
            Recensione.objects.create(
                prodotto=prodotto,
                utente=request.user,
                valutazione=valutazione,
                commento=commento
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Recensione aggiunta con successo'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Metodo non consentito'
    })


@login_required
@csrf_exempt
def carrello(request):
    user = request.user

    # Recupera tutti i prodotti associati all'ordine dell'utente
    ordini = OrdineProdotto.objects.filter(order__user=user, stato=False)

    # Inizializza lista per i prodotti nel carrello
    cart_items = []

    for ordine in ordini:
        prodotto = ordine.product  # Relazione diretta con il modello Prodotto
        if prodotto:
            # Recupera i dettagli del prodotto
            prodotto_nome = prodotto.nome
            prodotto_categoria = prodotto.categoria_descrizione
            immagini = prodotto.images.all()  
            image_url = immagini[0].image.url if immagini.exists() else None
            taglia_nome = ordine.taglia.nome if ordine.taglia else "Taglia non disponibile"
            taglia_id = ordine.taglia.id if ordine.taglia else None
            product_id = prodotto.id  # Aggiungi l'ID del prodotto

        else:
            prodotto_nome = "Prodotto non trovato"
            prodotto_categoria = "Categoria non trovata"
            image_url = None
            product_id = None  # Gestisci il caso in cui il prodotto non esiste

        # Aggiungi i dettagli all'oggetto ordine
        cart_items.append({
            'id': ordine.id,
            'nome': prodotto_nome,
            'categoria': prodotto_categoria,
            'quantity': ordine.quantity,
            'price': prodotto.prezzo if prodotto else 0,
            'image_url': image_url,
            'taglia_nome': taglia_nome,
            'taglia_id': taglia_id,
            'product_id': product_id,  # Aggiungi questa riga
        })

    # Calcola il totale del carrello
    cart_total = sum(item['quantity'] * item['price'] for item in cart_items)

    # Rendi i dati nella pagina 'order.html'
    return render(request, 'order.html', {'cart_products': cart_items, 'cart_total': cart_total})



@login_required
@csrf_exempt
def aggiorna_quantita(request):
    if request.method == "POST":
        try:
            # Legge i dati della richiesta
            data = json.loads(request.body)
            product_id = data.get('product_id')
            taglia_id = data.get('taglia_id')  # ID della taglia
            quantity = int(data.get('quantity'))

            # Verifica che la quantità sia valida
            if quantity < 1:
                return JsonResponse({"success": False, "message": "La quantità deve essere almeno 1."})

            # Recupera l'ordine attivo dell'utente
            ordine = Ordine.objects.filter(user=request.user, status='PENDING').first()
            if not ordine:
                return JsonResponse({"success": False, "message": "Nessun ordine attivo trovato."}, status=404)

            # Recupera l'associazione ProdottoTaglie
            prodotto_taglia = ProdottoTaglie.objects.filter(prodotto_id=product_id, taglia_id=taglia_id).first()
            if not prodotto_taglia:
                return JsonResponse({"success": False, "message": "Prodotto o taglia non trovati."}, status=404)

            # Verifica la disponibilità
            if quantity > prodotto_taglia.quantita:
                return JsonResponse({"success": False, "message": f"La quantità richiesta non è disponibile. Massimo: {prodotto_taglia.quantita}"})

            # Recupera il prodotto nel carrello
            ordine_prodotto = OrdineProdotto.objects.filter(order=ordine, product_id=product_id, taglia_id=taglia_id).first()
            if not ordine_prodotto:
                return JsonResponse({"success": False, "message": "Prodotto non trovato nel carrello."}, status=404)

            # Aggiorna la quantità nel carrello
            ordine_prodotto.quantity = quantity
            ordine_prodotto.save()

            # Aggiorna il totale dell'ordine
            ordine.total_amount = sum(
                op.product.prezzo * op.quantity for op in ordine.ordineprodotto_set.all()
            )
            ordine.save()

            # Restituisce il nuovo totale
            return JsonResponse({
                "success": True,
                "cart_total": ordine.total_amount,
                "product_total_price": ordine_prodotto.product.prezzo * ordine_prodotto.quantity
            })

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Errore: {str(e)}"}, status=500)

    return JsonResponse({"success": False, "message": "Metodo non consentito."}, status=405)

@login_required
@csrf_exempt
def aggiungi_al_carrello(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "message": "Utente non autenticato."}, status=403)

        data = json.loads(request.body)
        product_id = data.get("product_id")
        taglia_id = data.get("taglia_id")
        quantity = data.get("quantity", 1)

        try:
            prodotto = Prodotto.objects.get(id=product_id)
        except Prodotto.DoesNotExist:
            return JsonResponse({"success": False, "message": "Prodotto non trovato."}, status=404)

        try:
            prodotto_taglia = ProdottoTaglie.objects.get(prodotto=prodotto, taglia_id=taglia_id)
        except ProdottoTaglie.DoesNotExist:
            return JsonResponse({"success": False, "message": "Taglia non valida."}, status=404)

        if prodotto_taglia.quantita < quantity:
            return JsonResponse({"success": False, "message": f"Quantità non disponibile per questa taglia. Disponibile: {prodotto_taglia.quantita}."}, status=400)

        # Recupera l'ordine attivo (o ne crea uno nuovo)
        ordine, created = Ordine.objects.get_or_create(
            user=request.user,
            status='PENDING',
            defaults={"total_amount": 0, "delivery_address": ""}
        )

        # Aggiungi o aggiorna il prodotto con taglia nell'ordine
        ordine_prodotto, created = OrdineProdotto.objects.get_or_create(
            user_id=request.user.id,
            order_id=ordine.id,
            product_id=product_id,
            taglia_id=taglia_id,
            defaults={"quantity": quantity},
            stato = False
        )

        if not created:
            ordine_prodotto.quantity += quantity
            ordine_prodotto.save()

        # Aggiorna la quantità disponibile della taglia
        prodotto_taglia.quantita -= quantity
        prodotto_taglia.save()

        # Aggiorna il totale dell'ordine
        ordine.total_amount += prodotto.prezzo * quantity
        ordine.save()

        return JsonResponse({"success": True, "message": "Prodotto aggiunto al carrello."})

    return JsonResponse({"success": False, "message": "Metodo non consentito."}, status=405)


@login_required
@csrf_exempt
def rimuovi_dal_carrello(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "message": "Utente non autenticato."}, status=403)

        data = json.loads(request.body)
        product_id = data.get("product_id")
        taglia_id = data.get("taglia_id")
        quantity = data.get("quantity", 1)  # Quantità da rimuovere, default 1

        try:
            prodotto = Prodotto.objects.get(id=product_id)
        except Prodotto.DoesNotExist:
            return JsonResponse({"success": False, "message": "Prodotto non trovato."}, status=404)

        try:
            prodotto_taglia = ProdottoTaglie.objects.get(prodotto=prodotto, taglia_id=taglia_id)
        except ProdottoTaglie.DoesNotExist:
            return JsonResponse({"success": False, "message": "Taglia non valida."}, status=404)

        # Recupera l'ordine attivo
        try:
            ordine = Ordine.objects.get(user=request.user, status='PENDING')
        except Ordine.DoesNotExist:
            return JsonResponse({"success": False, "message": "Nessun carrello attivo trovato."}, status=404)

        # Trova il prodotto nell'ordine
        try:
            ordine_prodotto = OrdineProdotto.objects.get(
                user_id=request.user.id,
                order_id=ordine.id,
                product_id=product_id,
                taglia_id=taglia_id,
                stato=False
            )
        except OrdineProdotto.DoesNotExist:
            return JsonResponse({"success": False, "message": "Prodotto non trovato nel carrello."}, status=404)

        # Verifica che la quantità da rimuovere non sia maggiore di quella nel carrello
        if quantity > ordine_prodotto.quantity:
            quantity = ordine_prodotto.quantity  # Rimuovi tutto se la quantità richiesta è maggiore

        # Aggiorna o rimuovi il prodotto dall'ordine
        if ordine_prodotto.quantity > quantity:
            ordine_prodotto.quantity -= quantity
            ordine_prodotto.save()
        else:
            ordine_prodotto.delete()

        # IMPORTANTE: Incrementa la quantità disponibile della taglia (+1 per ogni unità rimossa)
        # Questo è il passaggio che ripristina la disponibilità del prodotto
        prodotto_taglia.quantita += quantity  # Fa +1 (o +quantity) alla quantità disponibile
        prodotto_taglia.save()

        # Aggiorna il totale dell'ordine
        ordine.total_amount -= prodotto.prezzo * quantity
        if ordine.total_amount < 0:
            ordine.total_amount = 0
        ordine.save()

        # Verifica se il carrello è vuoto e, in tal caso, elimina l'ordine
        if not OrdineProdotto.objects.filter(order_id=ordine.id, stato=False).exists():
            ordine.delete()
            return JsonResponse({
                "success": True, 
                "message": "Prodotto rimosso dal carrello. Carrello vuoto.",
                "empty_cart": True
            })

        return JsonResponse({
            "success": True, 
            "message": "Prodotto rimosso dal carrello.",
            "new_quantity": ordine_prodotto.quantity if ordine_prodotto.quantity > quantity else 0,
            "new_total": ordine.total_amount
        })

    return JsonResponse({"success": False, "message": "Metodo non consentito."}, status=405)



from django.http import JsonResponse
from django.utils import timezone
import json
from .models import Prodotto, Ordine, OrdineProdotto

@login_required
def checkout(request):
    user = request.user
    
    # Recupera l'ordine attivo dell'utente
    try:
        ordine = Ordine.objects.get(user=user, status='PENDING')
        ordini_prodotti = OrdineProdotto.objects.filter(order=ordine)
        prodotto = Prodotto.objects.all()
        taglia = Taglia.objects.all()
        
        # Verifica che ci siano prodotti nel carrello
        if not ordini_prodotti.exists():
            messages.error(request, "Il tuo carrello è vuoto.")
            return redirect('carrello')
            
        # Calcola il totale del carrello
        cart_total = sum(ordine_prodotto.quantity * ordine_prodotto.product.prezzo for ordine_prodotto in ordini_prodotti)
        
        # Aggiungi un attributo image_url a ciascun ordine con l'URL dell'immagine principale
        for ordine_prodotto in ordini_prodotti:
            immagini = ordine_prodotto.product.images.all()
            ordine_prodotto.image_url = immagini[0].image.url if immagini.exists() else None
            # Aggiungi anche il nome e la categoria del prodotto per il template
            ordine_prodotto.product_name = prodotto.get(id=ordine_prodotto.product.id).nome
            ordine_prodotto.product_categoria = prodotto.get(id=ordine_prodotto.product.id).categoria_descrizione
            ordine_prodotto.taglia_nome = taglia.get(id=ordine_prodotto.taglia.id).nome if ordine_prodotto.taglia else "Taglia non disponibile"
            ordine_prodotto.product_prezzo = prodotto.get(id=ordine_prodotto.product.id).prezzo

        
    except Ordine.DoesNotExist:
        messages.error(request, "Nessun ordine attivo trovato.")
        return redirect('carrello')
    
    
    
    # Se è una richiesta GET, mostra la pagina di checkout
    # Precompila i campi con i dati dell'utente se disponibili
    form_data = {
        'first_name': user.nome,
        'last_name': user.cognome,
        'email': user.email,
        'phone': user.numero_di_telefono or '',
        'address': user.indirizzo or '',
    }
    
    return render(request, 'checkout.html', {
        'cart_products': ordini_prodotti,
        'cart_total': cart_total,
        'form_data': form_data,
        'ordine': ordine  # Aggiungi l'ordine al contesto
    })



@csrf_exempt
def stripe_webhook(request):
    import stripe
    from django.conf import settings
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Payload non valido
        return JsonResponse({'error': str(e)}, status=400)
    except stripe.error.SignatureVerificationError as e:
        # Firma non valida
        return JsonResponse({'error': str(e)}, status=400)
    
    # Gestisci l'evento
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Recupera l'ID dell'ordine dai metadati
        ordine_id = session.get('metadata', {}).get('ordine_id')
        prodotto_ordine = OrdineProdotto.objects.filter(order__id=ordine_id)
        if ordine_id:
            try:
                ordine = Ordine.objects.get(id=ordine_id)
                ordine.status = 'SHIPPED' 
                ordine.save()
                prodotto_ordine.update(stato=True)

                
                # Qui puoi aggiungere altre azioni come inviare email di conferma, ecc.
                
            except Ordine.DoesNotExist:
                return JsonResponse({'error': 'Ordine non trovato'}, status=404)
    
    return JsonResponse({'success': True})



@login_required
def conferma_ordine(request, ordine_id):
    try:
        ordine = get_object_or_404(Ordine, id=ordine_id, user=request.user)
        ordine_prodotti = OrdineProdotto.objects.filter(order__id=ordine_id)

        
        # Verifica se il pagamento è stato completato
        session_id = request.GET.get('session_id')
        success = request.GET.get('success') == 'true'
        
        if session_id and success and ordine.stripe_session_id == session_id:
            # Il pagamento è stato completato con successo
            if ordine.status != 'SHIPPED':  # Verifica che l'ordine non sia già stato processato
                ordine.status = 'SHIPPED'
                ordine.save()
                try: 
                    subject = f'Conferma Ordine #{ordine.id:06d} - Mondaini Boutique'
                    
                    message = f"""
Gentile {request.user.nome} {request.user.cognome},

Grazie per il tuo ordine!

Dettagli dell'ordine:
Numero ordine: ORD-{ordine.id:06d}
Data: {ordine.order_date.strftime('%d/%m/%Y')}
Totale: €{ordine.total_amount}

Prodotti ordinati:
"""
                    
                    # Aggiungi i prodotti al messaggio
                    for prodotto in ordine_prodotti:
                        message += f"- {prodotto.product.nome} (Taglia: {prodotto.taglia.nome}) x{prodotto.quantity}: €{prodotto.product.prezzo}\n"
                    
                    message += f"""
Il tuo ordine verrà spedito a breve all'indirizzo:
{ordine.delivery_address}

Per qualsiasi domanda, non esitare a contattarci.

Cordiali saluti,
Il team di Mondaini Boutique
"""
                    # Invia l'email
                    send_mail(
                        subject,
                        message,
                        'andreabargilli@gmail.com' ,  # Email mittente (deve essere uguale a EMAIL_HOST_USER o un alias autorizzato)
                        [request.user.email],         # Email destinatario
                    )
                    
                except Exception as e:
                    print(f"Errore nell'invio dell'email: {e}")
                ordine_prodotti.update(stato=True)  # Aggiorna lo stato dei prodotti nell'ordine

                # Incrementa il conteggio degli acquisti per ogni prodotto nell'ordine
                for ordine_prodotto in ordine_prodotti:
                    prodotto = ordine_prodotto.product
                    prodotto.conteggio_acquisti += ordine_prodotto.quantity  # Incrementa in base alla quantità acquistata
                    prodotto.save()
                    
                    # Log per debug (opzionale)
                    print(f"Prodotto {prodotto.nome} - Vendite incrementate di {ordine_prodotto.quantity}. Totale: {prodotto.conteggio_acquisti}")
        
                
        for ordine_prodotto in ordine_prodotti:
            immagini = ordine_prodotto.product.images.all()
            ordine_prodotto.image_url = immagini[0].image.url if immagini.exists() else None
            ordine_prodotto.product_name = ordine_prodotto.product.nome
            ordine_prodotto.product_category = ordine_prodotto.product.categoria
            ordine_prodotto.taglia_nome = ordine_prodotto.taglia.nome
            
        return render(request, 'conferma_ordine.html', {
            'ordine': ordine,
            'ordini_prodotti': ordine_prodotti,
            'totale': ordine.total_amount,
            'data_ordine': ordine.order_date.strftime('%d/%m/%Y'),
            'numero_ordine': f"ORD-{ordine.id:06d}",
            'pagamento_completato': ordine.status == 'SHIPPED'
        })
        
    except Exception as e:
        messages.error(request, f"Errore nel recupero dell'ordine: {str(e)}")
        return redirect('index')


import stripe
from django.conf import settings
from django.http import JsonResponse
from .models import Ordine, OrdineProdotto

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def processa_ordine(request):
    """
    Endpoint per processare l'ordine dopo il checkout.
    Crea una sessione di checkout Stripe e restituisce l'URL.
    """
    if request.method == "POST" and request.user.is_authenticated:
        try:
            # Recupera l'ordine
            ordine_id = request.POST.get('ordine_id')
            
            # Debug: stampa l'ID dell'ordine
            print(f"ID ordine ricevuto: {ordine_id}")
            
            if not ordine_id:
                return JsonResponse({
                    'success': False,
                    'message': 'ID ordine mancante'
                }, status=400)
                
            ordine = get_object_or_404(Ordine, id=ordine_id, user=request.user)
            
            # Verifica che l'ordine sia in uno stato valido per il pagamento
            if ordine.status not in ['PENDING']:
                return JsonResponse({
                    'success': False,
                    'message': f'Stato ordine non valido per il pagamento: {ordine.status}'
                }, status=400)
            
            # Recupera i prodotti dell'ordine
            ordini_prodotti = OrdineProdotto.objects.filter(order=ordine)
            
            if not ordini_prodotti.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Nessun prodotto nell\'ordine'
                }, status=400)
            
            # Crea gli elementi per Stripe
            line_items = []
            for item in ordini_prodotti:
                product = item.product
                immagini = product.images.all()
                image_url = immagini[0].image.url if immagini.exists() else None
                
                line_items.append({
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': product.nome,
                            'description': product.categoria_descrizione or '',
                            'images': [request.build_absolute_uri(image_url)] if image_url else [],
                        },
                        'unit_amount': int(float(product.prezzo) * 100),  # Converti in centesimi
                    },
                    'quantity': item.quantity,
                })

            
            # Crea la sessione di checkout Stripe
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=request.build_absolute_uri(f'/conferma-ordine/{ordine.id}/') + '?success=true&session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri('/checkout/') + '?canceled=true',
                metadata={
                    'ordine_id': str(ordine.id),
                },
            )
            
            # Salva l'ID della sessione nell'ordine
            ordine.stripe_session_id = checkout_session.id
            ordine.save()
            
            # Debug: stampa l'URL della sessione
            print(f"Session URL: {checkout_session.url}")
            
            return JsonResponse({
                'success': True,
                'sessionId': checkout_session.id,
                'url': checkout_session.url,
            })
                
        except stripe.error.StripeError as e:
            print(f"Errore Stripe: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Errore Stripe: {str(e)}'
            }, status=500)
        except Exception as e:
            import traceback
            print(f"Errore generico: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': f'Errore: {str(e)}'
            }, status=500)
            
    return JsonResponse({
        'success': False,
        'message': 'Richiesta non valida'
    }, status=400)

from django.http import JsonResponse
from .models import Ordine, OrdineProdotto

@require_POST
@login_required
def salva_dati_spedizione(request):
    try:
        user = request.user
        ordine_id = request.POST.get('ordine_id')
        
        # Recupera i dati dal form
        nome = request.POST.get('first_name')
        cognome = request.POST.get('last_name')
        email = request.POST.get('email')
        telefono = request.POST.get('phone')
        indirizzo = request.POST.get('address')
        citta = request.POST.get('city')
        cap = request.POST.get('postal_code')
        paese = request.POST.get('country')
        
        # Validazione dei dati
        if not all([nome, cognome, email, telefono, indirizzo, citta, cap, paese]):
            return JsonResponse({
                'success': False,
                'message': 'Tutti i campi sono obbligatori'
            }, status=400)
        
        # Recupera l'ordine
        ordine = get_object_or_404(Ordine, id=ordine_id, user=user)
        
        # Aggiorna l'ordine con i dati di spedizione
        indirizzo_completo = f"{nome},{cognome}, {email}, {telefono},{indirizzo}, {citta}, {cap}, {paese}"
        ordine.delivery_address = indirizzo_completo
            
        ordine.save()
        
        # Aggiorna i dati dell'utente se necessario
        if hasattr(user, 'indirizzo') and user.indirizzo != indirizzo:
            user.indirizzo = indirizzo
        if hasattr(user, 'numero_di_telefono') and user.numero_di_telefono != telefono:
            user.numero_di_telefono = telefono
        if hasattr(user, 'nome') and user.nome != nome:
            user.nome = nome
        if hasattr(user, 'cognome') and user.cognome != cognome:
            user.cognome = cognome
        if hasattr(user, 'email') and user.email != email:
            user.email = email
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Dati di spedizione salvati con successo'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
    


from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

def contattaci(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        oggetto = request.POST.get('oggetto')
        messaggio = request.POST.get('messaggio')
        privacy = request.POST.get('privacy') == 'on'
        
        # Validazione
        if not all([nome, email, oggetto, messaggio, privacy]):
            messages.error(request, 'Per favore, compila tutti i campi e accetta la privacy policy.')
            return redirect('contattaci')
        
        # Costruisci il messaggio email
        messaggio_completo = f"""
        Nuovo messaggio da: {nome}
        Email: {email}
        
        Messaggio:
        {messaggio}
        """
        
        try:
            # Invia email all'amministratore
            send_mail(
                f'Nuovo contatto: {oggetto}',
                messaggio_completo,
                settings.DEFAULT_FROM_EMAIL,
                [settings.CONTACT_EMAIL],  # Imposta questa email nel tuo settings.py
                fail_silently=False,
            )
            
            # Invia email di conferma al cliente
            send_mail(
                'Grazie per averci contattato - Mondaini Boutique',
                f"""Gentile {nome},
                
                Grazie per averci contattato. Abbiamo ricevuto il tuo messaggio e ti risponderemo il prima possibile.

                Il tuo messaggio:
                {messaggio}

                Cordiali saluti,
                Il team di Mondaini Boutique
                                """,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            messages.success(request, 'Grazie! Il tuo messaggio è stato inviato con successo. Ti risponderemo al più presto.')
            return redirect('contattaci')
            
        except Exception as e:
            messages.error(request, f'Si è verificato un errore durante l\'invio del messaggio. Riprova più tardi o contattaci telefonicamente.')
            print(f"Errore nell'invio dell'email: {e}")
            return redirect('contattaci')
    
    return render(request, 'e_commerce/contattaci.html')



def i_piu_venduti(request):

    # Recupera i prodotti ordinati più frequentemente
    prodotti = Prodotto.objects.all().order_by('-conteggio_acquisti')[:10]  # I primi 10 più venduti

    # Passa i prodotti al template
    context = {
        'prodotti': prodotti,
    }
    return render(request, 'e_commerce/i_piu_venduti.html', context)




from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.contrib.auth.forms import PasswordResetForm

class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_dimenticata.html'
    form_class = PasswordResetForm
    success_url = reverse_lazy('password_reset_done')  # Redirect after successful form submission



def novita(request):
    # Recupera tutti i prodotti ordinati per data di creazione (dal più recente)
    prodotti = Prodotto.objects.all().order_by('-data_creazione')
    
    # Calcola i giorni trascorsi dalla creazione per ogni prodotto
    oggi = timezone.now().date()
    for prodotto in prodotti:
        giorni = (oggi - prodotto.data_creazione.date()).days
        prodotto.giorni_da_creazione = giorni
    
    return render(request, 'e_commerce/novita.html', {
        'prodotti': prodotti,
    })