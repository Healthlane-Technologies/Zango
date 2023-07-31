from sqlalchemy import Column, Integer, String, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from zelthy3.sql_alchemy import sa_base

if 'Tickets' not in sa_base.base.metadata.tables.keys():
    class Tickets(sa_base.base):
        __tablename__ = 'Tickets'
        __table_args__ = {'extend_existing': True}
        
        id = Column(Integer, primary_key=True)
        ticket_number = Column(String(100), nullable=False)
        user_id = Column(Integer, ForeignKey('MyUsers.id'), nullable=False)


if 'patient_instance' not in sa_base.base.metadata.tables.keys():
    patient_instance_association = Table('patient_instance', sa_base.base.metadata,
                                     Column('patient_id', Integer, ForeignKey('patients.id')),
                                     Column('instance_id', Integer, ForeignKey('instances.id')))

if 'associated_patients' not in sa_base.base.metadata.tables.keys():
    association_table = Table('associated_patients', sa_base.base.metadata,
        Column('patient_id', Integer, ForeignKey('patients.id')),
        Column('associated_patient_id', Integer, ForeignKey('patients.id'))
    )


if 'patients' not in sa_base.base.metadata.tables.keys():
    class Patient(sa_base.base):
        __tablename__ = 'patients'

        id = Column(Integer, primary_key=True)
        name = Column(String(50), nullable=False)
        age = Column(Integer, nullable=False)
        # gender = Column(String(10), nullable=False)
        phone = Column(String(15), nullable=False)
        email = Column(String(50), nullable=False)
        address = Column(String(200), nullable=False)
        doctor_id = Column(Integer, ForeignKey('doctors.id'))

        doctor = relationship('Doctor', back_populates='patients')
        prescriptions = relationship('Prescription', back_populates='patients')
        instances = relationship('Instance',
                             secondary=patient_instance_association
                             )
        associated_patients = relationship(
                                "Patient",
                                secondary=association_table,
                                primaryjoin=id==association_table.c.patient_id,
                                secondaryjoin=id==association_table.c.associated_patient_id,
                                backref="backrefs"
                            )


if 'doctors' not in sa_base.base.metadata.tables.keys():
    class Doctor(sa_base.base):
        __tablename__ = 'doctors'

        id = Column(Integer, primary_key=True)
        name = Column(String(50), nullable=False)
        specialization = Column(String(50), nullable=False)
        phone = Column(String(15), nullable=False)
        email = Column(String(50), nullable=False)

        patients = relationship('Patient', order_by=Patient.id, back_populates='doctor')
        prescriptions = relationship('Prescription', back_populates='doctors')
