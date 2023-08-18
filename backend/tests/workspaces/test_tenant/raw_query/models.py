from django.db import models
from zelthy.apps.dynamic_models.models import DynamicModelBase
from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField


class RawQueryAuthor(DynamicModelBase):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    dob = models.DateField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Protect against annotations being passed to __init__ --
        # this'll make the test suite get angry if annotations aren't
        # treated differently than fields.
        for k in kwargs:
            assert k in [f.attname for f in self._meta.fields], (
                "Author.__init__ got an unexpected parameter: %s" % k
            )


class RawQueryBook(DynamicModelBase):
    title = models.CharField(max_length=255)
    author = ZForeignKey(RawQueryAuthor, models.CASCADE)
    paperback = models.BooleanField(default=False)
    opening_line = models.TextField()


class RawQueryBookFkAsPk(DynamicModelBase):
    book = ZForeignKey(
        RawQueryBook, models.CASCADE, primary_key=True, db_column="not_the_default"
    )


class RawQueryCoffee(DynamicModelBase):
    brand = models.CharField(max_length=255, db_column="name")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)


class RawQueryMixedCaseIDColumn(DynamicModelBase):
    id = models.AutoField(primary_key=True, db_column="MiXeD_CaSe_Id")


# class Reviewer(DynamicModelBase):
#     reviewed = models.ManyToManyField(Book)


# class FriendlyAuthor(Author):
#     pass