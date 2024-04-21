import os
import uuid
import logging
import traceback
import inspect
import functools
from pathlib import Path
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.propagate import extract
from loguru import logger

from typing import List, Optional, Union
from opentelemetry.trace import Status, StatusCode, Tracer, get_current_span


tracer = trace.get_tracer(__name__)


def _zelthy_trace_func(wrapped_func, tracer: Tracer):
    @functools.wraps(wrapped_func)
    def _wrapper(*args, **kwargs):
        with tracer.start_as_current_span(
            wrapped_func.__module__ + "." + wrapped_func.__qualname__
        ) as span:
            try:
                result = wrapped_func(*args, **kwargs)
            except Exception as ex:
                span.set_status(Status(StatusCode.ERROR))
                span.record_exception(ex)
                raise ex

        return result

    return _wrapper

def zelthy_trace_methods(
    tracer: Tracer,
    only: Optional[Union[str, List[str]]] = None,
    exclude: Optional[Union[str, List[str]]] = None,
    abc: bool = False,
):
    """
    Automatically traces all public methods, or specific methods of a class depending
    on the arguments.

    You need to use this if you want to say, trace every implementation of an abstract
    method as decorating the method itself will get overriden by the subclasses where-as
    this metaclass will wrap the method when the subclass itself is created (the class
    not the instances!)

    If you want to use this metaclass and abc.ABC, use this and set abc=True.

    Using a metaclass is the python recommended way of automatically decorating
    all/some functions in a class.

    :param tracer: An otel Tracer, add `tracer = trace.get_tracer(__name__)` to the top
        of your file to get one.
    :param only: The name of the only function you want to trace or a list of names.
    :param exclude: The name of the function you do not want to trace or a list of
    names.
    :param abc: Whether this class should also be an abstract base class.
    """

    if only and not isinstance(only, list):
        only = [only]
    if exclude and not isinstance(exclude, list):
        exclude = [exclude]

    super_class = ABCMeta if abc else type

    class TraceMethodsMetaClass(super_class):
        def __new__(cls, name, bases, local):
            for attr in local:
                if cls._should_trace_attr(attr):
                    continue
                value = local[attr]
                if inspect.isfunction(value):
                    local[attr] = _zelthy_trace_func(value, tracer)
            return super().__new__(cls, name, bases, local)

        @staticmethod
        def _should_trace_attr(attr):
            return (
                attr.startswith("_")
                or (only and attr not in only)
                or (exclude and attr in exclude)
            )

    return TraceMethodsMetaClass