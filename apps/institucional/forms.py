from django import forms

from .models import MensagemContato
from .services import somente_digitos


class ContatoForm(forms.ModelForm):
    mensagem = forms.CharField(
        label="Mensagem",
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": "Descreva seu projeto ou dúvida..."}),
    )

    class Meta:
        model = MensagemContato
        fields = ["nome", "email", "telefone", "servico", "mensagem"]
        labels = {
            "nome": "Nome",
            "email": "E-mail",
            "telefone": "Telefone / WhatsApp",
            "servico": "Serviço de interesse",
        }
        widgets = {
            "nome": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "telefone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
        }

    def clean_telefone(self):
        telefone = self.cleaned_data["telefone"].strip()
        if not 10 <= len(somente_digitos(telefone)) <= 13:
            raise forms.ValidationError("Informe o telefone com DDD, ex.: (31) 99999-9999.")
        return telefone
