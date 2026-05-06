from zango.ai.tools.decorator import ToolParam, tool


@tool(
    name="get_patient_count",
    description="Return the total number of patients in the database",
    section="patients",
    timeout_seconds=10,
)
def get_patient_count() -> int:
    from .models import Patient
    return Patient.objects.count()


@tool(
    name="create_patient",
    description="Create a new patient record and return its ID",
    section="patients",
    timeout_seconds=10,
)
def create_patient(
    name: str = ToolParam(description="Patient full name"),
    age: int = ToolParam(description="Patient age in years"),
) -> dict:
    from .models import Patient
    p = Patient.objects.create(name=name, age=age)
    return {"id": p.pk, "name": p.name, "age": p.age}


@tool(
    name="get_patient_by_id",
    description="Retrieve a patient record by primary key",
    section="patients",
    timeout_seconds=10,
)
def get_patient_by_id(
    patient_id: int = ToolParam(description="The patient's primary key"),
) -> dict:
    from .models import Patient
    try:
        p = Patient.objects.get(pk=patient_id)
        return {"id": p.pk, "name": p.name, "age": p.age}
    except Patient.DoesNotExist:
        return {"error": f"Patient {patient_id} not found"}
