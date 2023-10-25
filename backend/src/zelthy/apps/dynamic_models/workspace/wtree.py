from collections import deque

class WorkspaceTreeNode:
    def __init__(self, value):
        self.value = value
        self.children = []

    def add_child(self, node):
        self.children.append(node)

    def remove_child(self, node):
        self.children.remove(node)

    def bfs(self):
        queue = deque([self])
        result = []
        while queue:
            node = queue.popleft()
            result.append(node.value)  # use append(node) to store nodes instead of values
            queue.extend(node.children)
        return result

    # def sorted_bfs(self):
    #     result []
    #     objects = self.bfs()

    def __str__(self, level=0):
        ret = "\t" * level + repr(self.value) + "\n"
        for child in self.children:
            ret += child.__str__(level + 1)
        return ret

    def __repr__(self):
        return '<TreeNode: {}>'.format(self.value)