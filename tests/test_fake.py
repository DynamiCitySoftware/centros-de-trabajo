from centros_de_trabajo.backends.fake import FakeBackend
from centros_de_trabajo.core.ordenes import Orden


def test_fake_acepta_las_cuatro_ordenes():
    backend = FakeBackend()
    for orden in Orden:
        assert backend.enviar(orden).ok
    assert backend.enviadas == list(Orden)