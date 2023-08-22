

class Lifecycle:

    """
        workspace lifecycle
    """

    def __init__(self, workspace: object) -> None:
        self.workspace = workspace

    @classmethod
    def launch(cls, params : dict) -> bool:
        pass

    def suspend(self) -> bool:
        pass

    def activate(self) -> bool:
        pass



    

