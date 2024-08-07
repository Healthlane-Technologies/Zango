from django.http import HttpResponseNotFound

from zango.test.cases import FastZangoTestCase
from zango.test.client import ZangoClient
from django.test import TestCase, override_settings, Client
from django.conf import settings
