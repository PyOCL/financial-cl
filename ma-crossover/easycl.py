import pyopencl as cl

class EasyCL:

  def prepare(self):
    self.context = cl.create_some_context()
    self.queue = cl.CommandQueue(clContext)

  def loadProgram(self, program):
    f = open('baseline.c', 'r')
    fstr = ''.join(f.readlines())
    return cl.Program(self.context, fstr).build()

  def createBuffer(flags, size=0, hostbuf=None):
    return cl.Buffer(context=self.context, flags=flags, size=size,
                     hostbuf=hostbuf)

  def run(program, *args):
    return program(*args)