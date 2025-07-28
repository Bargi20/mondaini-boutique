from decimal import Decimal
from unittest.mock import patch
from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
import json

import stripe
from .models import Prodotto, ProdottoTaglie, Taglia, Ordine, OrdineProdotto

User = get_user_model()  

class AggiungiAlCarrelloTestCase(TestCase):
    def setUp(self):
        # Creazione di un utente per i test
        self.user = User.objects.create_user(
            username='testuser', password='testpassword', ruolo='cliente'
        )

        # Creazione di un prodotto e taglia associata
        self.prodotto = Prodotto.objects.create(
            nome="T-shirt Test",
            prezzo=19.99,
            categoria="tshirt",
            tipo="uomo"
        )
        self.taglia = Taglia.objects.create(nome="M")
        self.prodotto_taglia = ProdottoTaglie.objects.create(
            prodotto=self.prodotto,
            taglia=self.taglia,
            quantita=10
        )

        self.url = reverse('add_to_cart')

    def test_utente_non_autenticato(self):
        # Verifica che un utente non autenticato ottenga un errore 302
        response = self.client.post(self.url, data=json.dumps({
            "product_id": self.prodotto.id,
            "taglia_id": self.taglia.id,
            "quantity": 1
        }), content_type="application/json")
        self.assertEqual(response.status_code, 302)  
        self.assertIn('/login/', response.url)

    def test_prodotto_non_trovato(self):
        # Effettua il login con l'utente di test
        self.client.login(username='testuser', password='testpassword')

        # Testa che un prodotto inesistente restituisca un errore 404
        response = self.client.post(self.url, data=json.dumps({
            "product_id": 999,  # ID inesistente
            "taglia_id": self.taglia.id,
            "quantity": 1
        }), content_type="application/json")
        self.assertEqual(response.status_code, 404)

    def test_quantita_non_disponibile(self):
        self.client.login(username='testuser', password='testpassword')

        response = self.client.post(self.url, data=json.dumps({
            "product_id": self.prodotto.id,
            "taglia_id": self.taglia.id,
            "quantity": 20  # Richiesta superiore alla quantità disponibile
        }), content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_aggiunta_prodotto_al_carrello(self):
        # Effettua il login con l'utente di test
        self.client.login(username='testuser', password='testpassword')

        response = self.client.post(self.url, data=json.dumps({
            "product_id": self.prodotto.id,
            "taglia_id": self.taglia.id,
            "quantity": 2
        }), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True, "message": "Prodotto aggiunto al carrello."})

        ordine = Ordine.objects.get(user=self.user, status="PENDING")
        ordine_prodotto = OrdineProdotto.objects.get(order=ordine, product=self.prodotto, taglia=self.taglia)

        self.assertEqual(ordine_prodotto.quantity, 2)
        self.assertEqual(ordine.total_amount, Decimal(str(self.prodotto.prezzo * 2)))




from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import json
from .models import Prodotto, ProdottoTaglie, Taglia, Ordine, OrdineProdotto

User = get_user_model()

class RimuoviDalCarrelloTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.client.login(username="testuser", password="testpassword")

        # Crea un prodotto e la taglia correttamente
        self.prodotto = Prodotto.objects.create(
            nome="Prodotto Test",
            prezzo=19.99,
            categoria='tshirt',
            tipo='uomo'
        )
        self.taglia_obj = Taglia.objects.create(nome='M')
        self.prodotto_taglia = ProdottoTaglie.objects.create(prodotto=self.prodotto, taglia=self.taglia_obj, quantita=10)

        # Crea un ordine e aggiungi un prodotto all'ordine
        self.ordine = Ordine.objects.create(
            user=self.user,
            status="PENDING",
            total_amount=19.99 * 2,  # supponiamo 2 pezzi nel carrello
            delivery_address="Via Test 123"
        )
        self.ordine_prodotto = OrdineProdotto.objects.create(
            user=self.user,
            order=self.ordine,
            product=self.prodotto,
            taglia=self.taglia_obj,
            quantity=2,
            stato=False
        )

        self.url = reverse("rimuovi_dal_carrello")

    def test_rimuovi_prodotto_successo(self):
        """Test che verifica la rimozione con successo di un prodotto dal carrello."""
        data = {
            "product_id": self.prodotto.id,
            "taglia_id": self.taglia_obj.id,
            "quantity": 1
        }
        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data["success"])
        
        expected_total = 19.99 * (2 - 1)
        self.assertAlmostEqual(float(response_data["new_total"]), expected_total, places=2)
        
        ordine_prodotto = OrdineProdotto.objects.get(id=self.ordine_prodotto.id)
        self.assertEqual(ordine_prodotto.quantity, 1)

    def test_prodotto_non_trovato(self):
        data = {
            "product_id": 999,
            "taglia_id": self.taglia_obj.id,
            "quantity": 1
        }
        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 404)
        response_data = response.json()
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Prodotto non trovato.")

    def test_taglia_non_valida(self):
        data = {
            "product_id": self.prodotto.id,
            "taglia_id": 999,
            "quantity": 1
        }
        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 404)
        response_data = response.json()
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Taglia non valida.")

    def test_quantita_maggiore_di_quella_nel_carrello(self):
        data = {
            "product_id": self.prodotto.id,
            "taglia_id": self.taglia_obj.id,
            "quantity": 5  # maggiore della quantità nel carrello (2)
        }
        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")
        
        # La view risponde con status 200 perché gestisce la rimozione anche se quantity > quantità presente
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        
        # Successo e messaggio di carrello vuoto
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["message"], "Prodotto rimosso dal carrello. Carrello vuoto.")
        self.assertTrue(response_data.get("empty_cart", False))
        
        self.assertNotIn("new_quantity", response_data)
        self.assertNotIn("new_total", response_data)
        
        # Verifica che l'ordine e il relativo OrdineProdotto siano stati eliminati
        self.assertFalse(Ordine.objects.filter(id=self.ordine.id).exists())
        self.assertFalse(OrdineProdotto.objects.filter(id=self.ordine_prodotto.id).exists())


    def test_utente_non_autenticato(self):
        self.client.logout()
        data = {
            "product_id": self.prodotto.id,
            "quantity": 1
        }
        response = self.client.post(self.url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 302)  # Redirect al login
        self.assertIn('/login', response.url)  # Verifica che rediriga alla pagina di login


    def test_metodo_non_consentito(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        response_data = response.json()
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["message"], "Metodo non consentito.")


class ProcessaOrdineTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.url = reverse('processa_ordine')

    def test_richiesta_get_non_valida(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'Richiesta non valida')

    def test_missing_ordine_id(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'ID ordine mancante')

    def test_invalid_status(self):
        self.client.login(username='testuser', password='testpassword')
        order = Ordine.objects.create(user=self.user, status='SHIPPED', total_amount=0, delivery_address='via')
        response = self.client.post(self.url, {'ordine_id': order.id})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Stato ordine non valido per il pagamento', data['message'])

    def test_empty_order(self):
        self.client.login(username='testuser', password='testpassword')
        order = Ordine.objects.create(user=self.user, status='PENDING', total_amount=0, delivery_address='via')
        response = self.client.post(self.url, {'ordine_id': order.id})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], "Nessun prodotto nell'ordine")

    @patch('stripe.checkout.Session.create')
    def test_stripe_error(self, mock_create):
        self.client.login(username='testuser', password='testpassword')
        order = Ordine.objects.create(user=self.user, status='PENDING', total_amount=0, delivery_address='via')
        prod = Prodotto.objects.create(nome='Test', prezzo=10, categoria='tshirt', tipo='uomo')
        size = Taglia.objects.create(nome='M')
        ProdottoTaglie.objects.create(prodotto=prod, taglia=size, quantita=5)
        OrdineProdotto.objects.create(user=self.user, order=order, product=prod, taglia=size, quantity=1, stato=False)
        mock_create.side_effect = stripe.error.StripeError('Stripe failure')
        response = self.client.post(self.url, {'ordine_id': order.id})
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Errore Stripe', data['message'])

    @patch('stripe.checkout.Session.create')
    def test_processa_ordine_success(self, mock_create):
        self.client.login(username='testuser', password='testpassword')
        order = Ordine.objects.create(user=self.user, status='PENDING', total_amount=0, delivery_address='via')
        prod = Prodotto.objects.create(nome='Test', prezzo=10, categoria='tshirt', tipo='uomo')
        size = Taglia.objects.create(nome='M')
        ProdottoTaglie.objects.create(prodotto=prod, taglia=size, quantita=5)
        OrdineProdotto.objects.create(user=self.user, order=order, product=prod, taglia=size, quantity=2, stato=False)
        # Mock stripe session
        mock_session = stripe.checkout.Session
        mock_session.id = 'sess_12345'
        mock_session.url = 'https://checkout.stripe.com/pay/sess_12345'
        mock_create.return_value = mock_session

        response = self.client.post(self.url, {'ordine_id': order.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['sessionId'], 'sess_12345')
        self.assertEqual(data['url'], 'https://checkout.stripe.com/pay/sess_12345')
        # Refresh order
        order.refresh_from_db()
        self.assertEqual(order.stripe_session_id, 'sess_12345')
