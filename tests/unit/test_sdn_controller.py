"""
Tests unitarios para SDN Controller
"""
import pytest


class TestSDNController:
    """Tests para SDN Controller"""
    
    def test_route_packet(self, container):
        """Test: enrutar un paquete"""
        controller = container.sdn_controller
        
        decision = controller.route_packet("NOISE-001")
        
        assert decision is not None
        assert decision.sensor_id == "NOISE-001"
        assert decision.selected_route in ["Ruta A (Larga)", "Ruta B (Corta)"]
    
    def test_get_route_stats(self, container):
        """Test: obtener estadísticas de rutas"""
        controller = container.sdn_controller
        stats = controller.get_route_stats()
        
        assert len(stats) == 2
        assert stats[0]['id'] in ['ROUTE_A', 'ROUTE_B']
