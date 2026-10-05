from rest_framework import serializers

from .models import Cita


class CitaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Cita
        fields = [
            'id',
            'cliente',
            'servicio',
            'peluquero',
            'tipo_peluquero',
            'fecha',
            'hora',
            'estado',
            'observaciones',
        ]
        read_only_fields = ['estado']