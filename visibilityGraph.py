import math, turtle

globalGraph = None
shortestPaths = None

def test():
    #specify polygons here:
    # !!!must be polygons, walls do not work!!!
    edgesRawRect = [[(-20,0),(-20,20)], [(20,20),(-20,20)], [(20,20),(20,0)], [(20,0),(-20,0)]]
    edgesRawRect2 = [[(0,85),(0,50)], [(0,85),(95,75)], [(95,75),(90,60)], [(90,60),(0,50)]]

    edgesRawTri = [[(30,30),(45,45)], [(45,45),(90,30)], [(30,30),(90,30)]]
    edgesRawTri2 = [[(-30,-30),(-60,-60)], [(-60,-60),(-90,-30)], [(-90,-30),(-30,-30)]]

    #edgesRawWall = [[(-60,90),(-65,10)],[(-65,10),(-30,-40)],[(-30,-40),(-25,-80)]]
    edgesRaw = edgesRawRect + edgesRawTri + edgesRawRect2

    startV,endV = Vertex(-50,-50),Vertex(90,100)
    vertices = [startV, endV]
    #vertices = []
    edges = []
    
    for e in edgesRaw:
        vs = []
        for vRaw in e:
            found = False
            for v in vertices:
                if v.x==vRaw[0] and v.y==vRaw[1]:
                    vs.append(v)
                    found=True
                    break
            if not found:
                newV = Vertex(*vRaw)
                vs.append(newV)
                vertices.append(newV)

        edges.append(Edge(*vs))

    g = Graph(vertices,edges,True)
    
    for k,v in g.edgeDic.items():
        #print(str(k)+': '+str([str(x) for x in v]))
        pass
	
    drawGraph(g,(startV,endV))
    global globalGraph
    globalGraph = g

class Vertex:

    def __init__(self, x: int, y: int, edges=[]):
        self.x,self.y = x,y
        self.edges = []
        self.polygonSet = None
        self.p  = None
        self.d = float('inf')

    def __repr__(self):
        return 'v({},{})'.format(self.x,self.y)


class Edge:

    def __init__(self,v1: 'Vertex', v2: 'Vertex'):
        assert(v1!=v2)
        self.v1,self.v2 = v1,v2
        self.vs = [v1,v2]
        self.vSet = set(self.vs)
        self.minX,self.maxX = (v1.x,v2.x) if v1.x<v2.x else (v2.x,v1.x)
        self.minY,self.maxY = (v1.y,v2.y) if v1.y<v2.y else (v2.y,v1.y)
        w = ((v2.x-v1.x)**2+(v2.y-v1.y)**2)**0.5

    def __str__(self):
        return '{}, {}'.format(*self.vs)
    

class Graph:

    def __init__(self, vertices, edges, isPolygonGraph=False):
        '''precond:
                -all edge in edges: (all v in edge, v in vertices)
                    => max(forAll v |e| for e in edges)
                -cycles form polygons i.e. don't cross
        '''
        
        self.vertices, self.edges = vertices, edges
        getOtherV = lambda e,v: e.v1 if e.v2==v else e.v2
        self.edgeDic = {v:[getOtherV(e,v) for e in edges if v in e.vs] for v in vertices}
        self.polygonSets = []

        if isPolygonGraph:
            self.createPolygonSet()

    def createPolygonSet(self):
        edgeDic = self.edgeDic.copy()
        
        def addToSet(_set,v):
            _set.add(v)
            v.polygonSet = _set
        
        while(len(edgeDic)>0):
            
            v = list(edgeDic.keys())[0]
            currSet = set()
            addToSet(currSet,v)
                
            if len(edgeDic[v])==0:
                
                self.polygonSets.append(currSet)
                edgeDic.pop(v)
                continue

            vOld = v
            v1 = edgeDic.pop(v)[0]
            addToSet(currSet,v1)
            
            while True:
                
                if len(edgeDic[v1])==1:
                    raise Exception('non-cyclic edges')
                
                assert(len(edgeDic[v1])<3)
                v2 = edgeDic.pop(v1)[0] if edgeDic[v1][1]==vOld else edgeDic.pop(v1)[1]
                addToSet(currSet,v2)
                
                if v2==v:
                    #we've come back to v origin, a complete polygon
                    break
                
                vOld = v1
                v1 = v2

            self.polygonSets.append(currSet)
            
        
                
    def getVisibilityGraph(self):
            
        vs, es = self.vertices, self.edges
        vsChecked = vs.copy()
        vg = es.copy()

        def edgesIntersect(ve,eObstacle):
            mcs = []
            
            if any(v in eObstacle.vs for v in ve.vs):
                return False
            
            for e in (ve,eObstacle):
                
                if e.v1.x==e.v2.x:
                    m,c = float('inf'), e.v1.x
                else:
                    m = (e.v2.y - e.v1.y)/(e.v2.x - e.v1.x)
                    c = e.v1.y - m*e.v1.x
                    
                mcs.append({'m':m,'c':c})
                
            if (mcs[0]['m']==mcs[1]['m']):
                return False

            if any(mc['m']==float('inf') for mc in mcs):
                
                line,notLine = (mcs[0],mcs[1]) if mcs[0]['m']==float('inf') else (mcs[1],mcs[0])
                x = line['c']
                y = notLine['m']*x + notLine['c']
                
            else:
                
                x = (mcs[0]['c']-mcs[1]['c'])/(mcs[1]['m']-mcs[0]['m'])
                y = mcs[0]['m']*x + mcs[0]['c']

            minX = max(ve.minX,eObstacle.minX)
            maxX = min(ve.maxX,eObstacle.maxX)
            minY = max(ve.minY,eObstacle.minY)
            maxY = min(ve.maxY,eObstacle.maxY)

            return minX <= x <= maxX and minY <= y <= maxY
        
        for vStart in vs:
            
            vsChecked.remove(vStart)
            
            for vEnd in vsChecked:
                vEndPoly = vEnd.polygonSet

                if vStart == vEnd:
                    continue

                ve = Edge(vStart,vEnd)
                
                blocked = False
                edgeExists = False

                if (vStart.polygonSet == vEnd.polygonSet):
                    continue
                                
                if not any(edgesIntersect(ve,e) for e in es):
                    vg.append(Edge(vStart,vEnd))

        return Graph(self.vertices,vg)


def dijkstra(g,s):
    assert s in g.vertices

    unvisited = set(g.vertices)
    edgeDic = g.edgeDic.copy()
    s.d = 0
    curr = s

    dist = lambda v1,v2: ((v2.x-v1.x)**2+(v2.y-v1.y)**2)**0.5

    while len(edgeDic)>0:
        
        vs = [_v for _v in edgeDic.pop(curr) if _v in unvisited]
        
        for v in vs:
            currDist = dist(curr,v)+curr.d
            
            if currDist < v.d:
            
                v.p = curr
                v.d = currDist

        unvisited.remove(curr)
        
        if not unvisited:
            break
        
        curr = min(unvisited, key=lambda v: v.d)

        
    
                
def drawGraph(g, startFin=None):
    t = turtle.Turtle()
    t.color('red','blue')
    t.hideturtle()
    t.penup()
    t.speed(0)

    if (startFin):
        startV,endV = startFin

        t.goto(startV.x+7,startV.y-7)
        t.write('start')
        t.goto(endV.x+7,endV.y-7)
        t.write('end')
        
    edgeDic = g.edgeDic.copy()
    
    def _drawVertex(v):
        t.penup()
        t.goto(v.x,v.y)
        t.pendown()
        t.circle(2)
        t.write(str(v))
        t.penup()
    
    def _drawEdge(v1,v2):
        t.penup()
        t.goto(v1.x,v1.y)
        t.pendown()
        t.goto(v2.x,v2.y)
        t.penup()


    def _drawVertexEdge(v1,v2):
        _drawVertex(v1)
        _drawEdge(v1,v2)
        _drawVertex(v2)
    
    while(len(edgeDic)>0):
        v = list(edgeDic.keys())[0]
            
        if len(edgeDic[v])==0:
            _drawVertex(v)
            edgeDic.pop(v)
            continue
        
        if v.polygonSet:
            t.begin_fill()
        vOld = v
        v1 = edgeDic.pop(v)[0]
        _drawVertexEdge(v,v1)
        
        while True:
            if len(edgeDic[v1])==1:
                edgeDic.pop(v1)
                break
            assert(len(edgeDic[v1])<3)

            v2 = edgeDic.pop(v1)[0] if edgeDic[v1][1]==vOld else edgeDic.pop(v1)[1]
            #the new v1 is the next edge in v2 that doesnt backtrack to
            #the current v1, which would otherwise create an infinite loop
            if v2==v:
                _drawVertexEdge(v1,v2)
                #we've come back to v origin, a complete polygon
                break
            _drawVertexEdge(v1,v2)
            vOld = v1
            v1 = v2
            
        if v.polygonSet:
            t.end_fill()

    vg = g.getVisibilityGraph()
    t.pencolor('green')
    for e in vg.edges:
        _drawEdge(e.v1,e.v2)

    if startFin:
        dijkstra(vg,startV)
        curr = endV
        t.pencolor('black')
        t.penup()
        t.goto(curr.x,curr.y)
        t.pendown()
        
        while curr.p != startV:
            t.goto(curr.p.x, curr.p.y)
            curr = curr.p
            
        t.goto(curr.p.x, curr.p.y)
        t.penup()


test()




























'''
class PolarCoord:

    def __init__(self, vStart: 'Vertex', vEnd: 'Vertex'):
        getHypo = lambda v1,v2: ((v2.x-v1.x)**2+(v2.y-v1.y)**2)**0.5

        def getAngle(v1,v2):
            ''''''return the sign-preserving angle between v1 and v2,
                with v1 as the origin''''''
            
            dX,dY = v2.x-v1.x,v2.y-v1.y
            quadrantAngle = math.degrees(math.atan(math.fabs(dX/dY))) if dY!=0 else 90
            assert(quadrantAngle>=0)
            if (dX>0 and dY>0):
                return quadrantAngle
            elif (dX<0 and dY>0):
                return quadrantAngle+90
            elif (dX<0 and dY<0):
                return quadrantAngle+180
            else:
                return quadrantAngle+270

        self.radius = getHypo(vStart,vEnd)
        self.angle = getAngle(vStart,vEnd)


    def isIntersected(self,p1: 'PolarCoord', p2: 'PolarCoord'):
        inAngle = min(p.angle for p in (p1,p2))<self.angle and self.angle<max(p.angle for p in (p1,p2))
        #inRange = self.radius<max(p.radius for p in (p1,p2))
        return inAngle and inRange
'''

            

                
                
            
            
