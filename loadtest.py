from locust import HttpUser, task, between
class Loadtest(HttpUser):
    wait_time = between(1,3)


    @task
    def test_mod_0(self):
        self.client.get('mod1/view0')

    @task
    def test_mod_1(self):
        self.client.get('mod1/view1')

    @task
    def test_mod_2(self):
        self.client.get('mod1/view2')

    @task
    def test_mod_3(self):
        self.client.get('mod1/view3')

    @task
    def test_mod_4(self):
        self.client.get('mod1/view4')

    @task
    def test_mod_5(self):
        self.client.get('mod1/view5')

    @task
    def test_mod_6(self):
        self.client.get('mod1/view6')

    @task
    def test_mod_7(self):
        self.client.get('mod1/view7')

    @task
    def test_mod_8(self):
        self.client.get('mod1/view8')

    @task
    def test_mod_9(self):
        self.client.get('mod1/view9')

    @task
    def test_mod_10(self):
        self.client.get('mod1/view10')

    @task
    def test_mod_11(self):
        self.client.get('mod1/view11')

    @task
    def test_mod_12(self):
        self.client.get('mod1/view12')

    @task
    def test_mod_13(self):
        self.client.get('mod1/view13')

    @task
    def test_mod_14(self):
        self.client.get('mod1/view14')

    @task
    def test_mod_15(self):
        self.client.get('mod1/view15')

    @task
    def test_mod_16(self):
        self.client.get('mod1/view16')

    @task
    def test_mod_17(self):
        self.client.get('mod1/view17')

    @task
    def test_mod_18(self):
        self.client.get('mod1/view18')

    @task
    def test_mod_19(self):
        self.client.get('mod1/view19')

    @task
    def test_mod_20(self):
        self.client.get('mod1/view20')

    @task
    def test_mod_21(self):
        self.client.get('mod1/view21')

    @task
    def test_mod_22(self):
        self.client.get('mod1/view22')

    @task
    def test_mod_23(self):
        self.client.get('mod1/view23')

    @task
    def test_mod_24(self):
        self.client.get('mod1/view24')

    @task
    def test_mod_25(self):
        self.client.get('mod1/view25')

    @task
    def test_mod_26(self):
        self.client.get('mod1/view26')

    @task
    def test_mod_27(self):
        self.client.get('mod1/view27')

    @task
    def test_mod_28(self):
        self.client.get('mod1/view28')

    @task
    def test_mod_29(self):
        self.client.get('mod1/view29')

    @task
    def test_mod_30(self):
        self.client.get('mod1/view30')

    @task
    def test_mod_31(self):
        self.client.get('mod1/view31')

    @task
    def test_mod_32(self):
        self.client.get('mod1/view32')

    @task
    def test_mod_33(self):
        self.client.get('mod1/view33')

    @task
    def test_mod_34(self):
        self.client.get('mod1/view34')

    @task
    def test_mod_35(self):
        self.client.get('mod1/view35')

    @task
    def test_mod_36(self):
        self.client.get('mod1/view36')

    @task
    def test_mod_37(self):
        self.client.get('mod1/view37')

    @task
    def test_mod_38(self):
        self.client.get('mod1/view38')

    @task
    def test_mod_39(self):
        self.client.get('mod1/view39')

    @task
    def test_mod_40(self):
        self.client.get('mod1/view40')

    @task
    def test_mod_41(self):
        self.client.get('mod1/view41')

    @task
    def test_mod_42(self):
        self.client.get('mod1/view42')

    @task
    def test_mod_43(self):
        self.client.get('mod1/view43')

    @task
    def test_mod_44(self):
        self.client.get('mod1/view44')

    @task
    def test_mod_45(self):
        self.client.get('mod1/view45')

    @task
    def test_mod_46(self):
        self.client.get('mod1/view46')

    @task
    def test_mod_47(self):
        self.client.get('mod1/view47')

    @task
    def test_mod_48(self):
        self.client.get('mod1/view48')

    @task
    def test_mod_49(self):
        self.client.get('mod1/view49')

    @task
    def test_mod_50(self):
        self.client.get('mod1/view50')

    @task
    def test_mod_51(self):
        self.client.get('mod1/view51')

    @task
    def test_mod_52(self):
        self.client.get('mod1/view52')

    @task
    def test_mod_53(self):
        self.client.get('mod1/view53')

    @task
    def test_mod_54(self):
        self.client.get('mod1/view54')

    @task
    def test_mod_55(self):
        self.client.get('mod1/view55')

    @task
    def test_mod_56(self):
        self.client.get('mod1/view56')

    @task
    def test_mod_57(self):
        self.client.get('mod1/view57')

    @task
    def test_mod_58(self):
        self.client.get('mod1/view58')

    @task
    def test_mod_59(self):
        self.client.get('mod1/view59')

    @task
    def test_mod_60(self):
        self.client.get('mod1/view60')

    @task
    def test_mod_61(self):
        self.client.get('mod1/view61')

    @task
    def test_mod_62(self):
        self.client.get('mod1/view62')

    @task
    def test_mod_63(self):
        self.client.get('mod1/view63')

    @task
    def test_mod_64(self):
        self.client.get('mod1/view64')

    @task
    def test_mod_65(self):
        self.client.get('mod1/view65')

    @task
    def test_mod_66(self):
        self.client.get('mod1/view66')

    @task
    def test_mod_67(self):
        self.client.get('mod1/view67')

    @task
    def test_mod_68(self):
        self.client.get('mod1/view68')

    @task
    def test_mod_69(self):
        self.client.get('mod1/view69')

    @task
    def test_mod_70(self):
        self.client.get('mod1/view70')

    @task
    def test_mod_71(self):
        self.client.get('mod1/view71')

    @task
    def test_mod_72(self):
        self.client.get('mod1/view72')

    @task
    def test_mod_73(self):
        self.client.get('mod1/view73')

    @task
    def test_mod_74(self):
        self.client.get('mod1/view74')

    @task
    def test_mod_75(self):
        self.client.get('mod1/view75')

    @task
    def test_mod_76(self):
        self.client.get('mod1/view76')

    @task
    def test_mod_77(self):
        self.client.get('mod1/view77')

    @task
    def test_mod_78(self):
        self.client.get('mod1/view78')

    @task
    def test_mod_79(self):
        self.client.get('mod1/view79')

    @task
    def test_mod_80(self):
        self.client.get('mod1/view80')

    @task
    def test_mod_81(self):
        self.client.get('mod1/view81')

    @task
    def test_mod_82(self):
        self.client.get('mod1/view82')

    @task
    def test_mod_83(self):
        self.client.get('mod1/view83')

    @task
    def test_mod_84(self):
        self.client.get('mod1/view84')

    @task
    def test_mod_85(self):
        self.client.get('mod1/view85')

    @task
    def test_mod_86(self):
        self.client.get('mod1/view86')

    @task
    def test_mod_87(self):
        self.client.get('mod1/view87')

    @task
    def test_mod_88(self):
        self.client.get('mod1/view88')

    @task
    def test_mod_89(self):
        self.client.get('mod1/view89')

    @task
    def test_mod_90(self):
        self.client.get('mod1/view90')

    @task
    def test_mod_91(self):
        self.client.get('mod1/view91')

    @task
    def test_mod_92(self):
        self.client.get('mod1/view92')

    @task
    def test_mod_93(self):
        self.client.get('mod1/view93')

    @task
    def test_mod_94(self):
        self.client.get('mod1/view94')

    @task
    def test_mod_95(self):
        self.client.get('mod1/view95')

    @task
    def test_mod_96(self):
        self.client.get('mod1/view96')

    @task
    def test_mod_97(self):
        self.client.get('mod1/view97')

    @task
    def test_mod_98(self):
        self.client.get('mod1/view98')

    @task
    def test_mod_99(self):
        self.client.get('mod1/view99')