from django.urls import path

from . import views


app_name = "lentes"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("kanban/", views.kanban, name="kanban"),
    path("retiradas/", views.retiradas, name="retiradas"),
    path("contato/", views.marcar_paciente_contatado, name="marcar_paciente_contatado"),
    path("retirada/", views.confirmar_retirada_paciente, name="confirmar_retirada_paciente"),
]
