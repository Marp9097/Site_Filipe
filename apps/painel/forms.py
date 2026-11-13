from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.text import slugify

from apps.institucional.models import ConfiguracaoSite, Depoimento
from apps.institucional.services import somente_digitos
from apps.portfolio.models import Categoria, Foto
from apps.portfolio.services import validar_arquivos


class EntrarForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Usuário ou senha incorretos.",
        "inactive": "Este usuário está desativado.",
    }


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "widget",
            MultipleFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
        )
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not data:
            if self.required:
                raise forms.ValidationError("Selecione ao menos uma foto.", code="required")
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        return [super(MultipleImageField, self).clean(arquivo, initial) for arquivo in data]


class FotoUploadForm(forms.Form):
    imagens = MultipleImageField(label="Fotos (JPG, PNG ou WEBP, até 10 MB cada, no máximo 20)")
    categoria = forms.ModelChoiceField(
        label="Categoria",
        queryset=Categoria.objects.all(),
        required=False,
        empty_label="Sem categoria",
    )

    def clean_imagens(self):
        arquivos = self.cleaned_data["imagens"]
        validar_arquivos(arquivos)
        return arquivos


class FotoForm(forms.ModelForm):
    class Meta:
        model = Foto
        fields = ["titulo", "categoria", "publicada", "ordem"]
        labels = {"publicada": "Publicada (aparece no site)"}


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nome", "ordem"]

    def clean_nome(self):
        nome = self.cleaned_data["nome"].strip()
        slug = slugify(nome)
        if not slug:
            raise forms.ValidationError("Use letras ou números no nome da categoria.")
        if Categoria.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Já existe uma categoria com esse nome.")
        return nome


class ConfiguracaoForm(forms.ModelForm):
    whatsapp = forms.CharField(label="WhatsApp", max_length=25)

    class Meta:
        model = ConfiguracaoSite
        fields = [
            "fundo",
            "modo_fotos",
            "telefone",
            "whatsapp",
            "email",
            "instagram",
            "cidade",
            "horario",
            "anos_experiencia",
        ]
        widgets = {
            "fundo": forms.RadioSelect,
            "modo_fotos": forms.RadioSelect,
        }
        help_texts = {
            "whatsapp": "Com DDI e DDD, só números. Ex.: 553193053178",
            "anos_experiencia": "Deixe em branco para não mostrar o contador no site.",
        }

    def clean_whatsapp(self):
        digitos = somente_digitos(self.cleaned_data["whatsapp"])
        if not 12 <= len(digitos) <= 13:
            raise forms.ValidationError("Informe o WhatsApp com DDI e DDD, ex.: 553193053178.")
        return digitos


class DepoimentoForm(forms.ModelForm):
    texto = forms.CharField(label="Depoimento", max_length=600, widget=forms.Textarea(attrs={"rows": 4}))
    nota = forms.TypedChoiceField(
        label="Nota",
        choices=[(n, f"{n} estrela{'s' if n > 1 else ''}") for n in range(5, 0, -1)],
        coerce=int,
        initial=5,
    )

    class Meta:
        model = Depoimento
        fields = ["nome", "empresa", "texto", "nota", "ativo", "ordem"]
