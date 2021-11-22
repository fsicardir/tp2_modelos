import requests
from pulp import LpProblem, LpMinimize, LpVariable, LpInteger, LpStatus, lpSum, value, PULP_CBC_CMD

def add_incompat(incompatibilities, name1, name2):
  incomp = incompatibilities.get(name1, set()) | {name2}
  incompatibilities[name1] = incomp

def add_time(times, name, time):
  times[name] = int(time)

def parse_file(lines):
  incompatibilities = {}
  times = {}

  for line in lines:
    fields = line.split()
    if fields[0] == 'e':
      add_incompat(incompatibilities, fields[1], fields[2])
      add_incompat(incompatibilities, fields[2], fields[1])
    if fields[0] == 'n':
      add_time(times, fields[1], fields[2])

  return times, incompatibilities

class Cloth:
  def __init__(self, name, time, incompatibles):
    self.name = name
    self.time = time
    self.incompatibles = incompatibles

  def __str__(self):
    return f'Cloth({self.name}, {self.time}, {self.incompatibles})'

  def __repr__(self):
    return self.__str__()

def create_clothes(times, incompats):
  clothes = []
  for name, time in times.items():
    clothes.append(Cloth(name, time, incompats.get(name, set())))
  return clothes

def is_compatible(cloth, batch):
  for c in batch:
    if c.name in cloth.incompatibles:
      return False
  return True

lines = requests.get("https://modelosuno.okapii.com/Problemas/segundo_problema.txt").text.split('\n')

lines = [line.strip() for line in lines][:-1]

times, incompats = parse_file(lines)

clothes = create_clothes(times, incompats)

# generate the adjacency matrix: connect incompatible clothes
adj_matrix = [[0 for l in range(len(clothes))] for l in range(len(clothes))]
for c in clothes:
  for inc in c.incompatibles:
    adj_matrix[int(c.name) - 1][int(inc) - 1] = 1
    adj_matrix[int(inc) - 1][int(c.name) - 1] = 1

n=43 # max colors: the greedy solution used 43 batches, so I asume the optimal solution will use less
nodes = range(len(clothes))
y=range(n)

#initializes lp problem
lp = LpProblem("Incompatibilities as Coloring Problem",LpMinimize)

# The problem variables are created
# variables x_ij to indicate whether node i is colored by color j;
xij = LpVariable.dicts("x",(nodes,y),0,1,LpInteger)

#variables yj to indicate whether color j was used
yj = LpVariable.dicts("y",y,0,1,LpInteger)

#objective is the sum of yj over all j
obj = lpSum(yj[j] for j in y)
lp += obj, "Objective Function"

#constraint: each node uses exactly 1 color
for r in nodes:
    jsum=0.0
    for j in y:
        jsum += xij[r][j]
    lp += jsum==1,""

#constraint: adjacent nodes do not have the same color
for row in range(len(adj_matrix)):
    for col in range(len(adj_matrix)):
        if adj_matrix[row][col]!=0:
            for j in y:
                lp += xij[row][j] + xij[col][j] <= 1,""

#constraint: if node i is assigned color k, color k is used
for i in nodes:
    for j in y:
        lp += xij[i][j]<=yj[j],""

#constraint for upper bound on # of colors used
lp += lpSum(yj[j] for j in y)<= n,""

#solves lp and prints optimal solution/objective value
lp.solve(PULP_CBC_CMD(gapRel=0.1,threads=8,msg=True))
status = str(LpStatus[lp.status])
print("Solution: "+ status)

print("Optimal Solution:")
print("Xij=1 values:")
for i in nodes:
	for j in y:
		if xij[i][j].value() == 1:
		          print(xij[i][j])

print("Yj values:")
for j in y:
    print(yj[j], yj[j].value())
print("Chromatic Number: ", value(lp.objective))

def write_solution(nodes, colors, xij, filename):
  with open(filename, 'w') as file:
    for i in nodes:
        for j in y:
            if xij[i][j].value() == 1:
                print(xij[i][j])
                file.write(f'{i} {j}\n')


write_solution(nodes, y, xij, 'segundo_problema.txt')
