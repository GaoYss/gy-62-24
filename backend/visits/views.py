from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from backend.common.http import error, list_response, ok, parse_json

from .models import VisitRecord
from .services import create_visit, list_visits, serialize_visit, update_visit


@require_http_methods(["GET", "OPTIONS"])
def dashboard_stats(request):
    from backend.appointments.models import Appointment

    today = timezone.localdate()
    today_start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
    today_end = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))

    checked_in_appointment_ids = VisitRecord.objects.values_list("appointment_id", flat=True)

    pending_checkin = Appointment.objects.filter(
        status="approved",
        visit_time__range=(today_start, today_end),
    ).exclude(pk__in=checked_in_appointment_ids).count()

    overdue_checkout = VisitRecord.objects.filter(check_out_time__isnull=True).count()

    return ok({
        "pending_checkin": pending_checkin,
        "overdue_checkout": overdue_checkout,
    })


@csrf_exempt
@require_http_methods(["GET", "POST", "OPTIONS"])
def visits_collection(request):
    if request.method == "GET":
        return list_response(list_visits())

    try:
        record = create_visit(parse_json(request))
        record.full_clean()
        record.save()
        record.appointment.status = "completed"
        record.appointment.save(update_fields=["status", "updated_at"])
        return ok(serialize_visit(record), status=201)
    except (ObjectDoesNotExist, ValidationError, IntegrityError, KeyError, TypeError, ValueError) as exc:
        return error(str(exc))


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE", "OPTIONS"])
def visit_detail(request, pk):
    record = get_object_or_404(VisitRecord.objects.select_related("appointment", "appointment__resident"), pk=pk)

    if request.method == "GET":
        return ok(serialize_visit(record))

    if request.method == "DELETE":
        record.delete()
        return ok({"deleted": True})

    try:
        record = update_visit(record, parse_json(request))
        record.full_clean()
        record.save()
        return ok(serialize_visit(record))
    except (ObjectDoesNotExist, ValidationError, IntegrityError, TypeError, ValueError) as exc:
        return error(str(exc))
