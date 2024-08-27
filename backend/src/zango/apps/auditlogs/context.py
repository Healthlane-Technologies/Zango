import contextlib
import time

from contextvars import ContextVar
from functools import partial

from django.db.models.signals import pre_save

from zango.apps.auditlogs.models import LogEntry


auditlog_value = ContextVar("auditlog_value")
auditlog_disabled = ContextVar("auditlog_disabled", default=False)


@contextlib.contextmanager
def set_actor(actor, remote_addr=None):
    """Connect a signal receiver with current user attached."""
    # Initialize thread local storage
    context_data = {
        "signal_duid": ("set_actor", time.time()),
        "remote_addr": remote_addr,
    }
    auditlog_value.set(context_data)

    # Connect signal for automatic logging
    set_actor = partial(_set_actor, user=actor, signal_duid=context_data["signal_duid"])
    pre_save.connect(
        set_actor,
        sender=LogEntry,
        dispatch_uid=context_data["signal_duid"],
        weak=False,
    )

    try:
        yield
    finally:
        try:
            auditlog = auditlog_value.get()
        except LookupError:
            pass
        else:
            pre_save.disconnect(sender=LogEntry, dispatch_uid=auditlog["signal_duid"])


def _set_actor(user, sender, instance, signal_duid, **kwargs):
    """Signal receiver with extra 'user' and 'signal_duid' kwargs.

    This function becomes a valid signal receiver when it is curried with the actor and a dispatch id.
    """
    from django.contrib.auth.models import User

    from zango.apps.appauth.models import AppUserModel
    from zango.apps.shared.platformauth.models import PlatformUserModel

    try:
        auditlog = auditlog_value.get()
    except LookupError:
        pass
    else:
        if signal_duid != auditlog["signal_duid"]:
            return
        if (
            sender == LogEntry
            and isinstance(user, AppUserModel)
            and instance.tenant_actor is None
        ):
            instance.tenant_actor = user
        elif (
            sender == LogEntry
            and isinstance(user, PlatformUserModel)
            and instance.platform_actor is None
        ):
            instance.platform_actor = user
        elif (
            sender == LogEntry
            and isinstance(user, User)
            and instance.platform_actor is None
        ):
            try:
                platform_user = PlatformUserModel.objects.get(user=user)
                instance.platform_actor = platform_user
            except Exception:
                pass
        instance.remote_addr = auditlog["remote_addr"]


@contextlib.contextmanager
def disable_auditlog():
    token = auditlog_disabled.set(True)
    try:
        yield
    finally:
        try:
            auditlog_disabled.reset(token)
        except LookupError:
            pass
