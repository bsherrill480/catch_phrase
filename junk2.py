from kivy.properties import NumericProperty
from kivy.event import EventDispatcher
class A(EventDispatcher):
    value = NumericProperty(0)
    def on_value(self, instance, value):
        print self, instance, value

a = A()
b = A()
a.value = 4
print "a", a.value
print "b", b.value

class B(object):
    value = []

c = B()
d = B()

c.value.append("cats")
print "c",c.value
print "d",d.value