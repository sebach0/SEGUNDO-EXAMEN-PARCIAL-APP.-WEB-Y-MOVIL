# PROJECT_VISION.md
# =========================================================
# Visión del Proyecto — Plataforma Inteligente de
# Atención de Emergencias Vehiculares
# =========================================================

## ¿Qué es?

Sistema digital para coordinar la atención de emergencias vehiculares.
Conecta propietarios de vehículos con talleres y técnicos especializados,
con trazabilidad completa a través de una bitácora de auditoría.

## Actores del sistema

| Actor               | Rol                                              |
|---------------------|--------------------------------------------------|
| Administrador       | Control total del sistema                        |
| Cliente             | Propietario de vehículos, solicita atención      |
| Técnico             | Mecánico asignado a un taller                    |
| Taller Responsable  | Gestiona el taller y su equipo de técnicos       |

## Ciclos de desarrollo

### Ciclo 1 — entregado (base)
- Acceso, Roles y Permisos
- Usuarios y Clientes
- Vehículos (marcas, modelos, tipos)
- Talleres y Técnicos
- Bitácora de auditoría

### Ciclo 2 — emergencias (en producto; implementación en backend + móvil + portal taller)
- Flujo: cliente reporta emergencia (API `/portal/cliente/emergencias`) → taller en bandeja, acepta o rechaza → asigna técnico (CU28) → operación y seguimiento (incl. técnico móvil).
- **Asistencia IA (modular):** el backend expone módulo `ai` (reglas, prioridad, payloads); STT y visión pesada pueden ejecutarse en un **contenedor opcional** `ai-inference` (Docker, perfil `ai`) con YOLO COCO o modelo de clasificación propio. Ver `ARCHITECTURE.md`, `HANDOFF_LATEST.md` y `DECISIONS_LOG` **DEC-010**.
- Geolocalización y notificaciones: pendientes o parciales según módulo (ver `CURRENT_STATE.md`).

### Ciclo 3 (futuro)
- Panel de estadísticas
- Reportes exportables
- Calificaciones y reviews
- Integración con servicios externos

**Nota de nomenclatura:** en código y comentarios históricos se usó «ciclo 3 fase n» para olas de implementación del dominio emergencias; el alcance de producto se alinea con **Ciclo 2** de esta visión.

## Stack tecnológico

| Capa      | Tecnología           |
|-----------|----------------------|
| Backend   | FastAPI + SQLAlchemy |
| Base dato | PostgreSQL 15        |
| Frontend  | Angular 17           |
| Móvil     | Flutter 3            |
| IA (opc.) | Worker Docker `ai-inference` (Whisper + Ultralytics); orquestado por backend |
| Deploy    | Docker + Azure VM    |
