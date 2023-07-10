from zelthy3.backend.datamodels import zmodels

class Patient(zmodels.Model):

    name = models.CharField(max_length=100)
    dob = models.DateField()



