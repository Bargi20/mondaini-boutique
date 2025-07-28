from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class Taglia(models.Model):
    nome = models.CharField(max_length=3)  # Nome della taglia (ad esempio, S, M, L)

    def __str__(self):
        return self.nome 


class Prodotto(models.Model):
    CATEGORIE_CHOICES = [
        ('pantaloni', 'Pantaloni'),
        ('tshirt', 'T-shirt'),
        ('cappotti', 'Cappotti'),
        ('camicie', 'Camicie'),
    ]

    TIPO_CHOICES = [
        ('bambino', 'bambino'),
        ('donna', 'donna'),
        ('uomo', 'uomo'),
    ]
    id = models.AutoField(primary_key=True)  # ID univoco generato automaticamente
    nome = models.CharField(max_length=100)  # Nome del capo di abbigliamento
    descrizione = models.TextField(blank=True, null=True)  # Descrizione del capo
    prezzo = models.DecimalField(max_digits=10, decimal_places=2)  # Prezzo del capo
    categoria = models.CharField(max_length=20,choices=CATEGORIE_CHOICES) # Select Categoria
    tipo = models.CharField(max_length=20,choices=TIPO_CHOICES) # Select Tipo
    data_creazione = models.DateTimeField(auto_now_add=True) # Data di creazione del prodotto
    conteggio_acquisti = models.IntegerField(default=0) # Conteggio degli acquisti
    
    @property
    def quantita_totale(self):
        # Somma le quantità di tutte le taglie associate
        return sum(taglia.quantita for taglia in self.taglie.all())

    def __str__(self):
        return self.nome

    @property
    def categoria_descrizione(self):
        """Ritorna la descrizione leggibile della categoria"""
        return dict(self.CATEGORIE_CHOICES).get(self.categoria, "Categoria sconosciuta")
    

class ProdottoTaglie(models.Model):
    prodotto = models.ForeignKey(Prodotto, related_name='prodotto_taglie', on_delete=models.CASCADE)
    taglia = models.ForeignKey(Taglia, on_delete=models.CASCADE)
    quantita = models.PositiveIntegerField(default=0)  # Quantità per la combinazione prodotto-taglia

    def __str__(self):
        return f"{self.prodotto.nome} - {self.taglia.nome} (Disponibile: {self.quantita})"

class ProductImage(models.Model):
    product = models.ForeignKey(Prodotto, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.nome}"

class CustomUser(AbstractUser):
    RUOLI_CHOICES = [
        ('admin', 'Admin'),
        ('cliente', 'Cliente'),
    ]

    # Campi aggiuntivi
    ruolo = models.CharField(max_length=20, choices=RUOLI_CHOICES, default='cliente')
    nome = models.CharField(max_length=50)
    cognome = models.CharField(max_length=50)
    indirizzo = models.TextField(blank=True, null=True)
    numero_di_telefono = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.ruolo})"


class Ordine(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SHIPPED', 'Shipped'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="orders")
    products = models.ManyToManyField(Prodotto, through='OrdineProdotto')
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_address = models.TextField()
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

class OrdineProdotto(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="ordine_prodotto")
    order = models.ForeignKey(Ordine, on_delete=models.CASCADE)
    product = models.ForeignKey(Prodotto, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    taglia = models.ForeignKey(Taglia, null=True, blank=True, on_delete=models.SET_NULL)
    stato = models.BooleanField(default=False)  # Stato del prodotto nell'ordine (ad esempio, se è stato spedito o meno)

    def __str__(self):
        return f"{self.product.nome} in Order #{self.order.id}"
    
class Recensione(models.Model):
    prodotto = models.ForeignKey(Prodotto, on_delete=models.CASCADE, related_name='recensioni')
    utente = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    valutazione = models.IntegerField(validators= [MinValueValidator(1), MaxValueValidator(5)])  # Valutazione da 1 a 5
    commento = models.TextField(blank=True, null=True)  # Commento dell'utente
    data_creazione = models.DateTimeField(auto_now_add=True)  # Data di creazione della recensione

    class Meta:
        unique_together = ('prodotto', 'utente')
        ordering = ['-data_creazione']

    def __str__(self):
        return f"Recensione di {self.utente.username} per {self.prodotto.nome}"