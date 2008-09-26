import gaphas
import math

from gaphas.matrix import Matrix
from gaphas.canvas import CanvasProjection
from gaphas.constraint import LineConstraint
from gaphas.item import NW, NE,SW, SE
#from gaphas.geometry import point_on_rectangle

EPSILON = 1e-6

def _update(variable, value):
    if abs(variable.value - value) > EPSILON:
        variable.value = value 

def _vec_length(vec):
    return pow(vec[0]*vec[0]+vec[1]*vec[1], 0.5)

def _point_on_rectangle(rect, p):
    W = rect[2]; H = rect[3]
    # decide on quarter
    # (-H, W) is perpendicular for W*y=H*x line
    # (H, W) is perpendicular for -W*y=H*x line
    # love dot products
    if -H*p[0] + W*p[1] >= 0: 
        if H*p[0] + W*p[1] >=0: # bottom quater
            point=(rect[0]+W/2,rect[1]+H)
        else: # left quater
            point=(rect[0],rect[1]+H/2)
    else:
        if H*p[0] + W*p[1] >=0: # right quater
            point=(rect[0]+W, rect[1]+H/2)
        else: # upper quater
            point=(rect[0]+W/2, rect[1])
    return point

def _get_radial(v):
    vlen = _vec_length(v)
    if vlen < 0.001: return 1, 0
        
    alpha = math.asin(v[1]/vlen)
    if v[0]<0: alpha=math.pi-alpha
    return vlen, alpha

def _side(handle, glued, view, item):
    handles = glued.handles()
    hx, hy = view.get_matrix_i2v(item).transform_point(handle.x, handle.y)
    ax, ay = view.get_matrix_i2v(glued).transform_point(handles[NW].x, handles[NW].y)
    bx, by = view.get_matrix_i2v(glued).transform_point(handles[SE].x, handles[SE].y)

    if abs(hx - ax) < 0.01:
        return handles[NW], handles[SW]
    elif abs(hy - ay) < 0.01:
        return handles[NW], handles[NE]
    elif abs(hx - bx) < 0.01:
        return handles[NE], handles[SE]
    else:
        return handles[SW], handles[SE]
    assert False


class NamedItem(gaphas.item.Item):
    "Item with the name"

    def __init__(self, name):
        gaphas.item.Item.__init__(self)
        self.name = name
        self.w = 1; self.h = 1

    def _calculate_text_width(self, context):
        cr = context.cairo
        self.w, self.h = gaphas.util.text_extents(cr, self.name)
        self.w, self.h = self.w, self.h

    def pre_update(self, context):
        self._calculate_text_width(context)

    def draw(self, context):
        cr = context.cairo
        gaphas.util.text_center(cr, 0, 0, self.name)


class RoundedRectangleItem(NamedItem):

    def draw(self, context):
        super(RoundedRectangleItem, self).draw(context)

        c = context.cairo

        if context.selected:
            c.set_source_rgba(0,0,1,1)
        elif context.hovered:
            c.set_source_rgba(0.5,0.5,1,1)
        else:
            c.set_source_rgba(0.,0.,0.)

        d = 8
        w = self.w+16
        h = self.h+16

        pi = math.pi
        c.move_to(-w/2, -h/2+d)
        c.arc(-w/2+d, -h/2+d, d, pi, 1.5 * pi)
        c.line_to(w/2-d, -h/2)
        c.arc(w/2-d, -h/2+d, d, 1.5 * pi, 0)
        c.line_to(w/2, h/2-d)
        c.arc(w/2-d, h/2-d, d, 0, 0.5 * pi)
        c.line_to(-w/2+d, h/2)
        c.arc(-w/2+d, h/2-d, d, 0.5 * pi, pi)
        c.close_path()

        c.stroke()

class EllipseItem(NamedItem):
    "Ellipse item with the name inside."

    def __init__(self, name):
        super(EllipseItem, self).__init__(name)
        handle = gaphas.item.Handle(movable=False)
        handle.visible = False
        self._handles.append(handle)
        self.center = handle
        self.name = name
        self.w = 1; self.h = 1
        self.color = (0,0,0,1)

    def draw(self, context):
        super(EllipseItem, self).draw(context)
        
        cr = context.cairo
        cr.save()
        if context.selected:
            cr.set_source_rgba(0,0,1,1)
        elif context.hovered:
            cr.set_source_rgba(0.5,0.5,1,1)
        else:
            cr.set_source_rgba(*self.color)
        gaphas.util.path_ellipse(cr, 0, 0, self.w+20, self.h+20)
        cr.stroke()
        cr.restore()

    def point(self, x, y):
        return 0
        
    def glue(self, item, handle, ix, iy):
        v = (ix,iy) # vector from center
        vlen, alpha = _get_radial(v)
        radius, point = self.intersect(alpha)
        distance = abs(vlen - radius)
        return (distance, point)

    def intersect(self, alpha):
        radius = math.pow(math.cos(alpha)/((self.w+20)/2.), 2) + math.pow(math.sin(alpha)/((self.h+20)/2.), 2)
        radius = 1/math.pow(radius, 0.5)
        point = (math.cos(alpha)*radius, math.sin(alpha)*radius)
        return (radius, point)

class RectangleItem(NamedItem):
    "Rectangle item with the name inside."

    def __init__(self, name):
        super(RectangleItem, self).__init__(name)
        handle = gaphas.item.Handle(movable=False)
        handle.visible = False
        self._handles.append(handle)
        self.center = handle

    def draw(self, context):
        super(RectangleItem, self).draw(context)
        
        cr = context.cairo
        cr.save()
        if context.selected:
            cr.set_source_rgba(0,0,1,1)
        elif context.hovered:
            cr.set_source_rgba(0.5,0.5,1,1)
        cr.rectangle(-self.w/2-5, -self.h/2-5, self.w+10, self.h+10)
        cr.stroke()

    def point(self, x, y):
        return 0
        
    def glue(self, item, handle, ix, iy):
        v = (ix, iy) # vector from center
        vlen, alpha = _get_radial(v)
        radius, point = self.intersect(alpha)
        distance = abs(vlen - radius)
        return (distance, point)

    def intersect(self, alpha):
        v = (math.cos(alpha), math.sin(alpha))
        point = _point_on_rectangle((-self.w/2-5, -self.h/2-5, self.w+10, self.h+10), v)
        return (_vec_length(point), point)


class MorphConstraint(gaphas.constraint.Constraint):
    "Keep variable on the outside boundary of the morph (figure)"
    
    def __init__(self, point, morph, oppositePoint = None):
        self.center = CanvasProjection(morph.center, morph)
        self.oppositePoint = oppositePoint
        variables = [point[0], point[1], self.center[0], self.center[1]]
        if oppositePoint:
            variables.extend((oppositePoint[0], oppositePoint[1]))
        super(MorphConstraint, self).__init__(*variables)

        self.point = point
        self.morph = morph
        if not oppositePoint:
            # remember alpha if there is no opposite morph present
            v = (self.point[0].value-self.center[0].value,
                 self.point[1].value-self.center[1].value)
            vlen, self.alpha = _get_radial(v)
        
    def solve_for(self, var):
        c = self.center
        p = self.point
        if self.oppositePoint:
            op = self.oppositePoint
            vlen, alpha = _get_radial((op[0].value-c[0].value, op[1].value-c[1].value))
        else:
            alpha = self.alpha
        vlen, v = self.morph.intersect(alpha)
        _update(self.point[0], self.center[0].value+v[0])
        _update(self.point[1], self.center[1].value+v[1])
        
class ConnectingTool(gaphas.tool.HandleTool):
    def glue(self, view, item, handle, wx, wy):
        """
        It allows the tool to glue to a Box or (other) Line item.
        The distance from the item to the handle is determined in canvas
        coordinates, using a 10 pixel glue distance.
        """
        if not handle.connectable:
            return

        # Make glue distance depend on the zoom ratio (should be about 10 pixels)
        inverse = Matrix(*view.matrix)
        inverse.invert()
        #glue_distance, dummy = inverse.transform_distance(10, 0)
        glue_distance = 10
        glue_point = None
        glue_item = None
        for i in view.canvas.get_all_items():
            if not i is item:
                v2i = view.get_matrix_v2i(i).transform_point
                ix, iy = v2i(wx, wy)
                try:
                    distance, point = i.glue(item, handle, ix, iy)
                    # Transform distance to world coordinates
                    #distance, dumy = matrix_i2w(i).transform_distance(distance, 0)
                    if distance <= glue_distance:
                        glue_distance = distance
                        i2v = view.get_matrix_i2v(i).transform_point
                        glue_point = i2v(*point)
                        glue_item = i
                except AttributeError:
                    pass
        if glue_point:
            v2i = view.get_matrix_v2i(item).transform_point
            handle.x, handle.y = v2i(*glue_point)
        return glue_item

    def connect(self, view, item, handle, wx, wy):
        def handle_disconnect():
            try:
                view.canvas.solver.remove_constraint(handle._connect_constraint)
            except KeyError:
                print 'constraint was already removed for', item, handle
                pass # constraint was alreasy removed
            else:
                print 'constraint removed for', item, handle
            handle._connect_constraint = None
            handle.connected_to = None
            # Remove disconnect handler:
            handle.disconnect = lambda: 0

        #print 'Handle.connect', view, item, handle, wx, wy
        glue_item = self.glue(view, item, handle, wx, wy)

        # drop old connection
        if handle.connected_to:
            handle.disconnect()

        if glue_item:
            if isinstance(glue_item, EllipseItem) or isinstance(glue_item, RectangleItem):

                # Make a constraint that keeps point on ellipse
                handle._connect_constraint = \
                        MorphConstraint(CanvasProjection(handle.pos, item),
                            glue_item)
            elif isinstance(glue_item, gaphas.examples.Box):
                h1, h2 = _side(handle, glue_item, view, item)

                # Make a constraint that keeps into account item coordinates.
                handle._connect_constraint = \
                        LineConstraint(line=(CanvasProjection(h1.pos, glue_item),
                            CanvasProjection(h2.pos, glue_item)),
                            point=CanvasProjection(handle.pos, item))

            view.canvas.solver.add_constraint(handle._connect_constraint)

            handle.connected_to = glue_item
            handle.disconnect = handle_disconnect

    def disconnect(self, view, item, handle):
        if handle.connected_to:
            #print 'Handle.disconnect', view, item, handle
            view.canvas.solver.remove_constraint(handle._connect_constraint)

