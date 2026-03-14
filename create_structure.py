import os
from pathlib import Path

base_dir = Path(r"c:\Trabajos UNT\CICLO VI EXT\SEMANA 07 LAB\Clase13 - ING.REQ\Sistema_GestiónEgresadosYOfertaLaboral")

structure = [
    "app.py",
    "docker-compose.yml",
    "Dockerfile",
    "README.md",
    "requirements.txt",
    ".streamlit/config.toml",
    "database/init.sql",
    "src/__init__.py",
    "src/config.py",
    "src/auth.py",
    "src/utils/__init__.py",
    "src/utils/database.py",
    "src/utils/session.py",
    "src/utils/validators.py",
    "src/models/__init__.py",
    "src/models/user.py",
    "src/pages/__init__.py",
    "src/pages/dashboard.py",
    "src/pages/perfil_mi_cuenta.py",
    "src/pages/egresados_lista.py",
    "src/pages/egresados_detalle.py",
    "src/pages/egresados_mi_perfil.py",
    "src/pages/empresas_lista.py",
    "src/pages/empresa_perfil.py",
    "src/pages/empleadores_gestion.py",
    "src/pages/ofertas_buscar.py",
    "src/pages/ofertas_gestionar.py",
    "src/pages/postulaciones_seguimiento.py",
    "src/pages/postulaciones_revisar.py",
    "src/pages/eventos_calendario.py",
    "src/pages/eventos_gestionar.py",
    "src/pages/pagos_mis_vouchers.py",
    "src/pages/pagos_admin.py",
    "src/pages/encuestas_responder.py",
    "src/pages/encuestas_disenar.py",
    "src/pages/encuestas_resultados.py",
    "src/pages/reportes_dashboard.py",
    "src/pages/notificaciones_centro.py",
    "src/pages/consultas_avanzadas.py",
    "src/pages/auditoria_bitacora.py",
    "tests/test_auth.py"
]

for file_path in structure:
    full_path = base_dir / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.touch(exist_ok=True)

print("Estructura creada con éxito.")
