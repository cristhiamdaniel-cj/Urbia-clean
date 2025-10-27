"""
Tests unitarios para TelemetryService
"""
import pytest


class TestTelemetryService:
    """Tests para TelemetryService"""
    
    def test_process_telemetry(self, container):
        """Test: procesar telemetría"""
        service = container.telemetry_service
        
        telemetry = service.process_telemetry(
            sensor_id="NOISE-001",
            value=65.5
        )
        
        assert telemetry is not None
        assert telemetry.value == 65.5
        assert str(telemetry.sensor_id) == "NOISE-001"
    
    def test_get_latest_telemetry(self, container):
        """Test: obtener última telemetría"""
        service = container.telemetry_service
        
        service.process_telemetry("NOISE-001", 60.0)
        service.process_telemetry("NOISE-001", 65.0)
        service.process_telemetry("NOISE-001", 70.0)
        
        latest = service.get_latest_telemetry("NOISE-001")
        
        assert latest is not None
        assert latest.value == 70.0
