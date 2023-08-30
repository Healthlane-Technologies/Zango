from locust import HttpUser, task, between

class Loadtest(HttpUser):
    wait_time = between(1,3)

    

    @task
    def test_mod_1(self):
        self.client.get('mod1/view1')

    # @task
    # def test_mod_3(self):
    #     self.client.get('mod3/view1')

    # @task
    # def test_mod_4(self):
    #     self.client.get('mod4/view1')

    # @task
    # def test_mod_5(self):
    #     self.client.get('mod5/view1')

    # @task
    # def test_mod_6(self):
    #     self.client.get('mod6/view1')

    # @task
    # def test_mod_7(self):
    #     self.client.get('mod7/view1')

    # @task
    # def test_mod_8(self):
    #     self.client.get('mod8/view1')

    # @task
    # def test_mod_9(self):
    #     self.client.get('mod9/view1')

    # @task
    # def test_mod_10(self):
    #     self.client.get('mod10/view1')

    # @task
    # def test_mod_11(self):
    #     self.client.get('mod11/view1')

    # @task
    # def test_mod_12(self):
    #     self.client.get('mod12/view1')

    # @task
    # def test_mod_13(self):
    #     self.client.get('mod13/view1')

    # @task
    # def test_mod_14(self):
    #     self.client.get('mod14/view1')

    # @task
    # def test_mod_15(self):
    #     self.client.get('mod15/view1')

    # @task
    # def test_mod_16(self):
    #     self.client.get('mod16/view1')

    # @task
    # def test_mod_17(self):
    #     self.client.get('mod17/view1')

    # @task
    # def test_mod_18(self):
    #     self.client.get('mod18/view1')

    # @task
    # def test_mod_19(self):
    #     self.client.get('mod19/view1')

    # @task
    # def test_mod_20(self):
    #     self.client.get('mod20/view1')

    # @task
    # def test_mod_21(self):
    #     self.client.get('mod21/view1')

    # @task
    # def test_mod_22(self):
    #     self.client.get('mod22/view1')

    # @task
    # def test_mod_23(self):
    #     self.client.get('mod23/view1')

    # @task
    # def test_mod_24(self):
    #     self.client.get('mod24/view1')

    # @task
    # def test_mod_25(self):
    #     self.client.get('mod25/view1')

    # @task
    # def test_mod_26(self):
    #     self.client.get('mod26/view1')

    # @task
    # def test_mod_27(self):
    #     self.client.get('mod27/view1')

    # @task
    # def test_mod_28(self):
    #     self.client.get('mod28/view1')

    # @task
    # def test_mod_29(self):
    #     self.client.get('mod29/view1')

    # @task
    # def test_mod_30(self):
    #     self.client.get('mod30/view1')

    # @task
    # def test_mod_31(self):
    #     self.client.get('mod31/view1')

    # @task
    # def test_mod_32(self):
    #     self.client.get('mod32/view1')

    # @task
    # def test_mod_33(self):
    #     self.client.get('mod33/view1')

    # @task
    # def test_mod_34(self):
    #     self.client.get('mod34/view1')

    # @task
    # def test_mod_35(self):
    #     self.client.get('mod35/view1')

    # @task
    # def test_mod_36(self):
    #     self.client.get('mod36/view1')

    # @task
    # def test_mod_37(self):
    #     self.client.get('mod37/view1')

    # @task
    # def test_mod_38(self):
    #     self.client.get('mod38/view1')

    # @task
    # def test_mod_39(self):
    #     self.client.get('mod39/view1')

    # @task
    # def test_mod_40(self):
    #     self.client.get('mod40/view1')

    # @task
    # def test_mod_41(self):
    #     self.client.get('mod41/view1')

    # @task
    # def test_mod_42(self):
    #     self.client.get('mod42/view1')

    # @task
    # def test_mod_43(self):
    #     self.client.get('mod43/view1')

    # @task
    # def test_mod_44(self):
    #     self.client.get('mod44/view1')

    # @task
    # def test_mod_45(self):
    #     self.client.get('mod45/view1')

    # @task
    # def test_mod_46(self):
    #     self.client.get('mod46/view1')

    # @task
    # def test_mod_47(self):
    #     self.client.get('mod47/view1')

    # @task
    # def test_mod_48(self):
    #     self.client.get('mod48/view1')

    # @task
    # def test_mod_49(self):
    #     self.client.get('mod49/view1')

    # @task
    # def test_mod_50(self):
    #     self.client.get('mod50/view1')

    # @task
    # def test_mod_51(self):
    #     self.client.get('mod51/view1')

    # @task
    # def test_mod_52(self):
    #     self.client.get('mod52/view1')

    # @task
    # def test_mod_53(self):
    #     self.client.get('mod53/view1')

    # @task
    # def test_mod_54(self):
    #     self.client.get('mod54/view1')

    # @task
    # def test_mod_55(self):
    #     self.client.get('mod55/view1')

    # @task
    # def test_mod_56(self):
    #     self.client.get('mod56/view1')

    # @task
    # def test_mod_57(self):
    #     self.client.get('mod57/view1')

    # @task
    # def test_mod_58(self):
    #     self.client.get('mod58/view1')

    # @task
    # def test_mod_59(self):
    #     self.client.get('mod59/view1')

    # @task
    # def test_mod_60(self):
    #     self.client.get('mod60/view1')

    # @task
    # def test_mod_61(self):
    #     self.client.get('mod61/view1')

    # @task
    # def test_mod_62(self):
    #     self.client.get('mod62/view1')

    # @task
    # def test_mod_63(self):
    #     self.client.get('mod63/view1')

    # @task
    # def test_mod_64(self):
    #     self.client.get('mod64/view1')

    # @task
    # def test_mod_65(self):
    #     self.client.get('mod65/view1')

    # @task
    # def test_mod_66(self):
    #     self.client.get('mod66/view1')

    # @task
    # def test_mod_67(self):
    #     self.client.get('mod67/view1')

    # @task
    # def test_mod_68(self):
    #     self.client.get('mod68/view1')

    # @task
    # def test_mod_69(self):
    #     self.client.get('mod69/view1')

    # @task
    # def test_mod_70(self):
    #     self.client.get('mod70/view1')

    # @task
    # def test_mod_71(self):
    #     self.client.get('mod71/view1')

    # @task
    # def test_mod_72(self):
    #     self.client.get('mod72/view1')

    # @task
    # def test_mod_73(self):
    #     self.client.get('mod73/view1')

    # @task
    # def test_mod_74(self):
    #     self.client.get('mod74/view1')

    # @task
    # def test_mod_75(self):
    #     self.client.get('mod75/view1')

    # @task
    # def test_mod_76(self):
    #     self.client.get('mod76/view1')

    # @task
    # def test_mod_77(self):
    #     self.client.get('mod77/view1')

    # @task
    # def test_mod_78(self):
    #     self.client.get('mod78/view1')

    # @task
    # def test_mod_79(self):
    #     self.client.get('mod79/view1')

    # @task
    # def test_mod_80(self):
    #     self.client.get('mod80/view1')

    # @task
    # def test_mod_81(self):
    #     self.client.get('mod81/view1')

    # @task
    # def test_mod_82(self):
    #     self.client.get('mod82/view1')

    # @task
    # def test_mod_83(self):
    #     self.client.get('mod83/view1')

    # @task
    # def test_mod_84(self):
    #     self.client.get('mod84/view1')

    # @task
    # def test_mod_85(self):
    #     self.client.get('mod85/view1')

    # @task
    # def test_mod_86(self):
    #     self.client.get('mod86/view1')

    # @task
    # def test_mod_87(self):
    #     self.client.get('mod87/view1')

    # @task
    # def test_mod_88(self):
    #     self.client.get('mod88/view1')

    # @task
    # def test_mod_89(self):
    #     self.client.get('mod89/view1')

    # @task
    # def test_mod_90(self):
    #     self.client.get('mod90/view1')

    # @task
    # def test_mod_91(self):
    #     self.client.get('mod91/view1')

    # @task
    # def test_mod_92(self):
    #     self.client.get('mod92/view1')

    # @task
    # def test_mod_93(self):
    #     self.client.get('mod93/view1')

    # @task
    # def test_mod_94(self):
    #     self.client.get('mod94/view1')

    # @task
    # def test_mod_95(self):
    #     self.client.get('mod95/view1')

    # @task
    # def test_mod_96(self):
    #     self.client.get('mod96/view1')

    # @task
    # def test_mod_97(self):
    #     self.client.get('mod97/view1')

    # @task
    # def test_mod_98(self):
    #     self.client.get('mod98/view1')

    # @task
    # def test_mod_99(self):
    #     self.client.get('mod99/view1')

    # @task
    # def test_mod_100(self):
    #     self.client.get('mod100/view1')
