from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cita
from .serializers import CitaSerializer

class CitaCreateView(APIView):
    def post(self,request):
        serializer = CitaSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        datos = serializer.validated_data

        try:
            cita =Cita.crear_cita(
                cliente=datos['cliente'],   
                servicio=datos['servicio'],
                fecha=datos['fecha'],
                hora=datos['hora'],
                tipo_peluquero=datos.get('tipo_peluquero', 'CUALQUIERA'),
                peluquero=datos.get('peluquero'),
                observaciones=datos.get('observaciones', ''),
            )
        except ValidationError as e:
            return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)  

        respuesta = CitaSerializer(cita)

        return Response(respuesta.data, status=status.HTTP_201_CREATED)