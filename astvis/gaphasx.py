import logging
from astvis.common import FINE, FINER, FINEST
LOG = logging.getLogger(__name__)

import math

import gaphas
import gaphas.util
from gaphas.matrix import Matrix
from gaphas.constraint import LineConstraint
from gaphas.item import NW, NE,SW, SE
from gaphas.canvas import CanvasProjection

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

    PADX=10
    PADY=10
    MIN_WIDTH=0
    MIN_HEIGHT=0

    def __init__(self, name):
        gaphas.item.Item.__init__(self)
        self.name = name
        self.w = 1; self.h = 1

        handle = gaphas.item.Handle(movable=False,
                                    strength=gaphas.connector.VERY_STRONG)
        handle.visible = False
        self._handles.append(handle)
        self.center = handle        

    def _calculate_text_width(self, context):
        cr = context.cairo
        self.w, self.h = gaphas.util.text_extents(cr, self.name)
        self.w, self.h = self.w, self.h

    def pre_update(self, context):
        self._calculate_text_width(context)

    def draw(self, context):
        cr = context.cairo
        gaphas.util.text_center(cr, 0, 0, self.name)


class MorphItem:

    def intersect(self, alpha):
        "Implement in subclass"
        raise NotImplemented


class RoundedRectangleItem(NamedItem,MorphItem):

    RADIUS=8

    def intersect(self, alpha):
        # currently rectange item intersection
        v = (math.cos(alpha), math.sin(alpha))
        w = max((self.w+self.PADX*2), self.MIN_WIDTH)
        h = max((self.h+self.PADY*2), self.MIN_HEIGHT)
        point = _point_on_rectangle((-w/2, -h/2, w, h), v)
        return (_vec_length(point), point)

    def draw(self, context):
        super(RoundedRectangleItem, self).draw(context)

        c = context.cairo

        if context.selected:
            c.set_source_rgba(0,0,1,1)
        elif context.hovered:
            c.set_source_rgba(0.5,0.5,1,1)
        else:
            c.set_source_rgba(0.,0.,0.)

        d = self.RADIUS
        w = self.w+self.PADX*2
        h = self.h+self.PADY*2

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

class EllipseItem(NamedItem, MorphItem):
    "Ellipse item with the name inside."

    def __init__(self, name):
        super(EllipseItem, self).__init__(name)
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
        
        w = max((self.w+self.PADX*2), self.MIN_WIDTH)
        h = max((self.h+self.PADY*2), self.MIN_HEIGHT)

        gaphas.util.path_ellipse(cr, 0, 0, w, h)
        cr.stroke()
        cr.restore()

    def point(self, p):
        return 0

    def intersect(self, alpha):
        w = max((self.w+self.PADX*2), self.MIN_WIDTH)
        h = max((self.h+self.PADY*2), self.MIN_HEIGHT)
        radius = math.pow(math.cos(alpha)/(w/2.), 2) + math.pow(math.sin(alpha)/(h/2.), 2)
        radius = 1/math.pow(radius, 0.5)
        point = (math.cos(alpha)*radius, math.sin(alpha)*radius)
        return (radius, point)

class RectangleItem(NamedItem,MorphItem):
    "Rectangle item with the name inside."

    def __init__(self, name):
        super(RectangleItem, self).__init__(name)

    def draw(self, context):
        super(RectangleItem, self).draw(context)
        
        cr = context.cairo
        cr.save()
        if context.selected:
            cr.set_source_rgba(0,0,1,1)
        elif context.hovered:
            cr.set_source_rgba(0.5,0.5,1,1)
        w = max((self.w+self.PADX*2), self.MIN_WIDTH)
        h = max((self.h+self.PADY*2), self.MIN_HEIGHT)
        cr.rectangle(-w/2, -h/2, w, h)
        cr.stroke()

    def point(self, p):
        return 0

    def intersect(self, alpha):
        v = (math.cos(alpha), math.sin(alpha))
        w = max((self.w+self.PADX*2), self.MIN_WIDTH)
        h = max((self.h+self.PADY*2), self.MIN_HEIGHT)
        point = _point_on_rectangle((-w/2, -h/2, w, h), v)
        return (_vec_length(point), point)


class DiamondItem(NamedItem,MorphItem):
    "Diamond item with the name inside."

    PADX = 3.
    PADY = 3.

    def __init__(self, name):
        super(DiamondItem, self).__init__(name)

    def draw(self, context):
        super(DiamondItem, self).draw(context)
        
        cr = context.cairo
        cr.save()
        if context.selected:
            cr.set_source_rgba(0,0,1,1)
        elif context.hovered:
            cr.set_source_rgba(0.5,0.5,1,1)
        # w,h - textbox width and height
        w = max((self.w+self.PADX*2), self.MIN_WIDTH)
        h = max((self.h+self.PADY*2), self.MIN_HEIGHT)
        # dw, dh - diamond width and height
        dw, dh = self._getDiamondSize(w,h)
        cr.move_to(-dw/2, 0)
        cr.line_to(0, dh/2)
        cr.line_to(dw/2, 0)
        cr.line_to(0, -dh/2)
        cr.line_to(-dw/2, 0)
        cr.stroke()

    def _getDiamondSize(self, w, h):
        dh = h*2
        # so that diamond lines touch the textbox
        # the formula: dw * dh = w * dh + h * dw
        dw = (w * dh)/(dh - h)
        return dw, dh

    def point(self, p):
        return 0

    def intersect(self, alpha):
        v = (math.cos(alpha), math.sin(alpha))
        w = max((self.w+self.PADX*2), self.MIN_WIDTH)
        h = max((self.h+self.PADY*2), self.MIN_HEIGHT)
        point = _point_on_rectangle((-w/2, -h/2, w, h), v)

        dw, dh = self._getDiamondSize(w,h)
        dpoint = (point[0]*dw/w, point[1]*dh/h)
        return (_vec_length(dpoint), dpoint)

class MorphConstraint(gaphas.constraint.Constraint):
    "Keep variable on the outside boundary of the morph (figure)"
    
    def __init__(self, point, morph, oppositePoint = None, line=None):
        self.center = morph.canvas.project(morph, morph.center)
        self.line = line

        self.point = point
        
        if isinstance(point, CanvasProjection):
            origPoint = point._point
        else:
            origPoint = point

        if oppositePoint!=None:
            self.oppositePoint = oppositePoint
        elif line!=None and origPoint in (line._handles[0].pos, line._handles[-1].pos):
            canvas = line.canvas
            if origPoint==line._handles[0].pos:
                self.oppositePoint = canvas.project(line, line._handles[1])
            elif origPoint==line._handles[-1].pos:
                self.oppositePoint = canvas.project(line, line._handles[-2])
        else:
            self.oppositePoint = None        

        variables = [point[0], point[1], self.center[0], self.center[1]]
        if oppositePoint:
            variables.extend((oppositePoint[0], oppositePoint[1]))
        super(MorphConstraint, self).__init__(*variables)

        self.morph = morph
        if not self.oppositePoint:
            # remember alpha if there is no opposite morph present
            v = (self.point[0].value-self.center[0].value,
                 self.point[1].value-self.center[1].value)
            vlen, self.alpha = _get_radial(v)
        else:
            self.alpha = None

        LOG.log(FINER, "Morph constraint with opposite point %s and angle %s",
                self.oppositePoint, self.alpha)
        
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


def DefaultTool():
    tool = gaphas.tool.ToolChain()
    tool.append(gaphas.tool.HoverTool())
    tool.append(gaphas.tool.ConnectHandleTool())
    tool.append(gaphas.tool.ItemTool())
    tool.append(gaphas.tool.RubberbandTool())
    return tool

class MorphBoundaryPort(gaphas.connector.PointPort):

    def __init__(self, pos, morphItem):
        assert isinstance(morphItem, MorphItem)
        
        super(MorphBoundaryPort, self).__init__(pos)
        self.item = morphItem


    def constraint(self, canvas, line, handle, glue_item):        
        c = MorphConstraint(canvas.project(line, handle.pos),
                            glue_item,
                            line=line)
        return c

    def glue(self, pos):
        vlen, alpha = _get_radial(pos)
        radius, point = self.item.intersect(alpha)
        distance = abs(vlen - radius)
        return point, distance
