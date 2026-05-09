"""ODIN-Hunter | Private Program Tracker"""
class PrivatePrograms:
    def __init__(self): self.programs = []
    def add(self, program): self.programs.append(program)
    def get_all(self): return self.programs
