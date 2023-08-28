from django.db import models
from django.contrib.postgres.fields import JSONField
# from django.utils.translation import ugettext_lazy as _

from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField, ZManyToManyField


class SkuModel(DynamicModelBase):
  """
  Model for SKUs
  """
  label = models.CharField(
                  "SKU Label",
                  max_length=255,
                   )
  brand_name = models.CharField(
                  "Brand Name",
                  max_length=255,
                  blank=True
                  )
  pack_size = models.CharField(
                  "Pack Size",
                  max_length=255,
                  blank=True
                  )
  mrp = models.FloatField(
                  "MRP including Taxes",
                  null=True,
                  blank=True
                  )
  molecule = models.CharField(
                  "Molecule",
                  max_length=255,
                  blank=True
                  )
  manufacturer = models.CharField(
                  "Manufacturer",
                  max_length=255,
                  blank=True
                  )
  is_active = models.BooleanField(
                  "Is active",
                  default=True
                  )
  is_free = models.BooleanField(
                  "Is Free",
                  default=False
                  )
  extrafield1_char = models.CharField(
                  "Extra Field1 Char",
                  max_length=255,
                  blank=True
                  )
  extrafield2_char = models.CharField(
                  "Extra Field2 Char",
                  max_length=255,
                  blank=True
                  )
  extrafield3_char = models.CharField(
                  "Extra Field3 Char",
                  max_length=255,
                  blank=True
                  )

  jsonfield_extra1 = JSONField(null=True, blank=True)


  def __str__(self):
    return self.label
  


class SkuTypes(DynamicModelBase):
  """
  Model to store types of SKU's as paid, free, discount etc.
  """
  label = models.CharField(
                       "SKU Types (e.g. Paid, Frre, 75% discount)",
                       max_length=255,
                       unique=True
                       )
  is_active = models.BooleanField(
                      "Is active",
                      default=True
                      )

  def __str__(self):
    return self.label
  

class OrderItemsModel(DynamicModelBase):
  """
  Model for order Items
  """
  label = models.CharField(
                   "Item Label",
                  max_length=255,
                   )
  sku = ZForeignKey(SkuModel, on_delete=models.CASCADE)
  quantity = models.IntegerField(
                     "Quantity",
                     default=0)
  discount = models.FloatField(
                     "Discount",
                     default=0
                     )
  item_type = ZForeignKey(
                      SkuTypes,
                      null=True,
                      blank=True,
                      on_delete=models.CASCADE
                      )
  is_active = models.BooleanField(
                  "Is active",
                  default=True
                  )

  def __str__(self):
    return "%s (%s %s)" %(self.label,  self.quantity, self.sku.pack_size)