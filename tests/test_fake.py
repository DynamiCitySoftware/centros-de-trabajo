from centros_de_trabajo.backends.fake import FakeBackend
from centros_de_trabajo.core.ordenes import Orden


def test_fake_acepta_las_cuatro_ordenes():
    backend = FakeBackend()
    for orden in Orden:
        assert backend.enviar(orden, 7).ok
    assert backend.enviadas == [(orden, 7) for orden in Orden]