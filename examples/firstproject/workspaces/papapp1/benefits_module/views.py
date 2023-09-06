from django.views import View
from django.http import JsonResponse

from rest_framework import status
from rest_framework.response import Response  # Not woring with View
from rest_framework.views import APIView # Not woring properly : for get kwargs is {}

from .models import BenefitsModel, BenefitsDispensingModel
from . serializers import BenefitsModelSerializer
from ..program_module.models import ProgramModel
from .models import DispensingOptionsModel, DispensingOptionsOrderItemsModel, OrderItemsModel, BenefitsSupplyChainNodes
from ..supplychainnode_module.models import SupplyChainNodes
# from .. patient_module.models import DoctorModel, Patient
from ..test_module.models import CityModel

from .serializers import DispensingOptionsModelSerializer

from zelthy.apps.appauth.models import UserRoleModel


class BenefitView(View):
    def get(self, request, *args, **kwargs):
        _id = request.GET.get('id')
        if _id:
            try:
                benefit = BenefitsModel.objects.get(id=_id)
                # print("benefit_type => ", benefit.get_benefit_type_display())
                serializer = BenefitsModelSerializer(benefit)
                context = {"success": True, "data": serializer.data}
                return JsonResponse(context, status=status.HTTP_200_OK)
            except:
                context = {"success": False, "msg": "Please give valid benefit id."}
                return JsonResponse(context, status=status.HTTP_404_NOT_FOUND)
            
        context = {"success": False, "msg": "Please give benefit id."}
        return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request, *args, **kwargs):
        serializer = BenefitsModelSerializer(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            context = {"success": True, "msg": "Benefit addedd successfully..!", "data": serializer.data}
            return JsonResponse(context, status=status.HTTP_201_CREATED)
        else:
            context = {"success": False, "msg": "Benefit addedd failed..!", "error": serializer.errors}
        return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)


class BenefitGetView(View):
    def get(self, request, *args, **kwargs):
        get_benefits_by = request.GET.get("get_benefits_by")
        benefits = None
        if get_benefits_by == 'all':
            benefits = BenefitsModel.objects.all()
        elif get_benefits_by == 'program' and request.GET.get('program_id'):
            program_id = request.GET.get('program_id')
            benefits = BenefitsModel.objects.filter(program_id=program_id)
        else:
            context = {"success": False,"msg": "Invalid get_benefits_by."}
            return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = BenefitsModelSerializer(benefits, many=True)
        context = {"success": True, "data": serializer.data}
        return JsonResponse(context, status=status.HTTP_200_OK)
    

class BenefitRunView(View):
    def get(self, request, *args, **kwargs):
        # program_id = request.GET.get("program_id")
        # benefits_id = request.GET.get("benefits_id")

        # if program_id:
        #     program = ProgramModel.objects.filter(id=program_id).first()
        #     if program:
        #         prog_data = {
        #             "program_id": program.id,
        #             "short_code": program.short_code,
        #             "program_name": program.program_name
        #         }

        
        # program=ProgramModel.objects.filter(benefits__short_code='teleconsultation-benefit')
        # print("program by benefit short code", program)

        # program=ProgramModel.objects.get(id=2)
        # print("programs all benefits", program.benefits.all())

        # benefit = BenefitsModel()
        # benefit.short_code = "fourth-benefit"
        # benefit.label = "Fourth-Consultation"
        # benefit.benefit_type = "other"
        # benefit.benefit_category = "free"
        # benefit.program = ProgramModel.objects.get(id=2)
        # benefit.save()

        # print(benefit)
       
       
       
        return JsonResponse({"success": True}, status=status.HTTP_200_OK)



        
        
        # serializer = BenefitsModelSerializer(benefits, many=True)
        # context = {"success": True, "data": serializer.data}
        # return JsonResponse(context, status=status.HTTP_200_OK)



############################## --- ####### --- #########################

class DispensingOptionsView(View):
    def get(self, request, *args, **kwargs):
        _id = request.GET.get('id')
        if _id:
            try:
                benefit = DispensingOptionsModel.objects.get(id=_id)
                serializer = DispensingOptionsModelSerializer(benefit)
                context = {"success": True, "data": serializer.data}
                return JsonResponse(context, status=status.HTTP_200_OK)
            except:
                context = {"success": False, "msg": "Please give valid dispensing id."}
                return JsonResponse(context, status=status.HTTP_404_NOT_FOUND)
            
        context = {"success": False, "msg": "Please give dispensing id."}
        return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request, *args, **kwargs):
        serializer = DispensingOptionsModelSerializer(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            context = {"success": True, "msg": "dispensing addedd successfully..!", "data": serializer.data}
            return JsonResponse(context, status=status.HTTP_201_CREATED)
        else:
            context = {"success": False, "msg": "dispensing addedd failed..!", "error": serializer.errors}
        return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)
    








### ------------  API to run scripts ------------- ###
class RunScript(View):
    def post(self, request, *args, **kwargs):

        print("kwargs ---post--====----> ", kwargs)

        # #Worked
        # dispensingoption = DispensingOptionsModel.objects.get(id=1)
        # item = OrderItemsModel.objects.get(id=1)
        # DispensingOptionsOrderItemsModel.objects.create(dispensingoption=dispensingoption, items=item)

        # #Worked
        # dispensingoption = DispensingOptionsModel.objects.get(id=1)
        # item = OrderItemsModel.objects.get(id=2)
        # DispensingOptionsOrderItemsModel.objects.create(dispensingoption=dispensingoption, items=item)

        # #Worked
        # item = OrderItemsModel.objects.get(id=2)
        # objs = DispensingOptionsOrderItemsModel.objects.filter(items=item)
        # print(objs)
        # print("----------")
        # for obj in objs:
        #     print(obj.items.label)



        # # Worked
        # dispensingoption = DispensingOptionsModel.objects.get(id=2)
        # benefit = BenefitsModel.objects.get(id=1)
        # obj = BenefitsDispensingModel()
        # obj.dispensingoption = dispensingoption
        # obj.benefit_id = benefit.id
        # obj.save()


        # # Worked
        # dispensingoption = DispensingOptionsModel.objects.get(id=1)
        # benefit = BenefitsModel.objects.get(id=2)
        # obj = BenefitsDispensingModel()
        # obj.dispensingoption = dispensingoption
        # obj.benefit_id = benefit.id
        # obj.save()








        # benefit = BenefitsModel.objects.get(id=1)
        # scn_executor_nodes = SupplyChainNodes.objects.get(id=2)
        # obj = BenefitsSupplyChainNodes()
        # obj.scn_executor_nodes = scn_executor_nodes
        # obj.benefit_id = benefit.id
        # obj.save()



        # Tesing Properties
        # program=ProgramModel.objects.get(id=2)
        # print(program)
        # # print("program.has_free_benefits() ==> ", program.has_free_benefits())
        # print("program.get_all_linked_benefits() ==> ", program.get_all_linked_benefits())

        # print("program.generate_program_condition() ==> ", program.generate_program_condition())

        

        # print("program.generate_program_condition() ==> ", program.generate_program_condition())


        
        # benefit=BenefitsModel.objects.get(id=2)
        # print("benefit.generate_order_extrastatus_12_condition() ==> ", benefit.generate_order_extrastatus_12_condition())
        # print("benefit.get_min_credit_reqd() ==> ", benefit.get_min_credit_reqd()) # Faild - Many To Many Not available

        # print("benefit.get_config() ==> ", benefit.get_config()) # Fail - has no attribute 'benefitorderconfig_set'

        # print("benefit ==> ", benefit)



        # obj = UserRoleModel()
        # obj.name = "Manager Admin"
        # obj.save()

        
        # obj = Patient()
        # obj.name = "test pat2"
        # obj.address = "address dkfjg dfkjg "
        # obj.save()
        # print("patient")
        # data = {"name": obj.name, "address": obj.address}


        
        # prog_objs = [ProgramModel(short_code='sc101', program_name='prog_101', description='This is desc.101bsdf ksdfjb.'),
        #             ProgramModel(short_code='sc202', program_name='prog_202', description='This is desc.101bsdf ksdfjb.'),
        #             ProgramModel(short_code='sc303', program_name='prog_303', description='This is desc.101bsdf ksdfjb.')]

        # ProgramModel.objects.bulk_create(prog_objs)


        # doc_objs = [DoctorModel(doctor_name='doc 1'),
        #             DoctorModel(doctor_name='doc 2'),
        #             DoctorModel(doctor_name='doc 3')]
        
        # DoctorModel.objects.bulk_create(doc_objs)



        # pat_objs = [Patient(name='pat 1', doctor_id=1),
        #             Patient(name='pat 2', doctor_id=2),
        #             Patient(name='pat 3', doctor_id=2)]
        
        # Patient.objects.bulk_create(pat_objs)

        # DoctorModel.objects.get(id=2).delete()

        # DoctorModel.objects.filter(id=3).update(doctor_name='doc 1001')



        # city_objs = [CityModel(city_name='city 1'),
        #             CityModel(city_name='city 2'),
        #             CityModel(city_name='city 3')]
        
        # CityModel.objects.bulk_create(city_objs)



        # doc_objs = [DoctorModel(doctor_name='doc 1', city_id = 1),
        #             DoctorModel(doctor_name='doc 2', city_id = 2),
        #             DoctorModel(doctor_name='doc 3', city_id = 2)]
        
        # DoctorModel.objects.bulk_create(doc_objs)



        # CityModel.objects.get(id=1).delete()



        return JsonResponse({"success": True}, status=status.HTTP_200_OK)
    



    def put(self, request, *args, **kwargs):
        print("kwargs --put--==> ", kwargs)
        return JsonResponse({"success": True}, status=status.HTTP_200_OK)


    def patch(self, request, *args, **kwargs):
        print("kwargs --patch--==> ", kwargs)
        return JsonResponse({"success": True}, status=status.HTTP_200_OK)


    def delete(self, request, *args, **kwargs):
        print("kwargs --patch--==> ", kwargs)
        return JsonResponse({"success": True}, status=status.HTTP_200_OK)