import random

BW = 10
NUM = 8

f = open("/users/mdolati/transiver/tr_mx", "w")

for i in range(NUM):
  cur_bw = BW
  for j in range(NUM):
    if i == j:
      new_bw = 0.0
    else:
      new_bw = random.uniform(0,cur_bw)
    f.write("%s " %new_bw)
    cur_bw -= new_bw
  f.write("\n")

f.close()
